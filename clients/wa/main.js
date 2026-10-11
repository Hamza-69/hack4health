// WhatsApp client: links a WhatsApp number as a device (Baileys) and is the client side of the agent API.
//
// Each incoming message waits out DEBOUNCE_SECONDS with any that follow it, then the batch goes to
// the core's POST /agent/messages with this client's token. Voice notes, photos and PDFs first go to
// POST /agent/media, which turns each into a text message. The core POSTs the agent's replies to
// /messages with a reply token, and they go out on WhatsApp.
//
// The linked session lives in auth/; delete it to link another number. Open http://localhost:<PORT>
// to scan the QR code. State other than the session is in memory.

import { rm } from 'node:fs/promises'
import { createServer } from 'node:http'

import makeWASocket, {
  Browsers, DisconnectReason, downloadMediaMessage, fetchLatestBaileysVersion, getContentType, isJidBroadcast,
  isJidGroup, isJidNewsletter, isJidStatusBroadcast, isLidUser, isPnUser, jidDecode, jidNormalizedUser,
  normalizeMessageContent, useMultiFileAuthState,
} from 'baileys'
import { createRemoteJWKSet, jwtVerify } from 'jose'
import pino from 'pino'
import QRCode from 'qrcode'

try { process.loadEnvFile('.env') } catch {} // CLIENT_TOKEN, written by `uv run h4h init`
const CORE_URL = process.env.CORE_URL ?? 'http://localhost:8000'
const CLIENT_TOKEN = process.env.CLIENT_TOKEN
const PORT = Number(process.env.PORT ?? 9001)
const DEBOUNCE = Number(process.env.DEBOUNCE_SECONDS ?? 2) * 1000
// Optional: only answer these numbers (comma-separated, any format). Everyone else is ignored.
const ALLOW = new Set((process.env.WA_ALLOW ?? '').split(',').map(n => n.replace(/\D/g, '')).filter(Boolean))
const AUTH_DIR = 'auth'
const AUDIENCE = 'client:wa'
const ISSUER = 'h4h-core'
const TYPING_FOR = 120_000 // stop showing "typing…" if no reply comes within this long
const SORRY = 'Sorry, something went wrong on our side. Please try again in a moment.\nعذراً، صار في مشكلة عنّا. جرّب كمان شوي.'

const logger = pino({ level: process.env.BAILEYS_LOG_LEVEL ?? 'error' })
const jwks = createRemoteJWKSet(new URL(`${CORE_URL}/.well-known/jwks.json`))

let sock = null
let qr = null // QR code to scan while no number is linked
let linked = null // the linked number, while connected

const jids = new Map() // account id -> the chat to reply in
const chains = new Map() // account id -> promise: one user's messages are read in order
const reading = new Map() // account id -> messages still being read (media uploads)
const pending = new Map() // account id -> texts waiting out the debounce
const timers = new Map() // account id -> debounce timer
const typing = new Map() // account id -> timer refreshing "typing…"
const outbox = [] // replies that arrived while WhatsApp was disconnected

// --- WhatsApp connection ---

async function connect() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR)
  const { version } = await fetchLatestBaileysVersion().catch(() => ({}))
  sock = makeWASocket({
    auth: state,
    logger,
    browser: Browsers.macOS('Wasel'),
    shouldSyncHistoryMessage: () => false,
    ...(version && { version }),
  })
  sock.ev.on('creds.update', saveCreds)
  sock.ev.on('connection.update', onConnection)
  sock.ev.on('messages.upsert', ({ messages, type }) => {
    if (type !== 'notify') return // history, not new messages
    for (const m of messages) receive(m).catch(e => console.error('could not handle a message:', e))
  })
}

async function onConnection({ connection, lastDisconnect, qr: code }) {
  if (code) {
    // The code changes every 20s or so; the page always shows the current one.
    if (!qr) console.log(`No number linked yet. Open http://localhost:${PORT} and scan the QR code with the phone that has Wasel's number.`)
    qr = code
  }
  if (connection === 'open') {
    qr = null
    linked = `+${jidDecode(sock.user.id).user}`
    console.log(`Linked to ${linked}. Listening for messages.`)
    for (const { jid, text } of outbox.splice(0)) await deliver(jid, text)
  }
  if (connection === 'close') {
    linked = null
    const status = lastDisconnect?.error?.output?.statusCode
    let wait = 3000
    if (status === DisconnectReason.loggedOut) {
      console.log('The number was unlinked from the phone. Scan the new QR code to link one again.')
      await rm(AUTH_DIR, { recursive: true, force: true })
      wait = 0
    } else if (status === DisconnectReason.restartRequired) {
      wait = 0 // normal right after scanning the QR code
    } else if (status === DisconnectReason.connectionReplaced) {
      console.log('Another client took over this WhatsApp session (is it running on a second laptop?). Retrying in 30s.')
      wait = 30_000
    } else {
      console.log(`WhatsApp connection closed (${status ?? lastDisconnect?.error?.message}). Reconnecting.`)
    }
    setTimeout(() => connect().catch(e => console.error('reconnect failed:', e)), wait)
  }
}

// --- Incoming messages ---

async function receive(m) {
  const jid = m.key.remoteJid
  if (m.key.fromMe || !jid || isJidGroup(jid) || isJidBroadcast(jid) || isJidStatusBroadcast(jid) || isJidNewsletter(jid)) return
  const read = reader(normalizeMessageContent(m.message), m)
  if (!read) return // reactions, stickers, receipts and other noise
  const account = await accountOf(m.key)
  if (!account || (ALLOW.size && !ALLOW.has(account.replace(/\D/g, '')))) return
  jids.set(account, jid)
  sock.readMessages([m.key]).catch(() => {})
  startTyping(account)
  reading.set(account, (reading.get(account) ?? 0) + 1)
  const done = (chains.get(account) ?? Promise.resolve())
    .then(read)
    .then(texts => {
      texts = texts.filter(Boolean)
      if (texts.length) pending.set(account, [...(pending.get(account) ?? []), ...texts])
    })
    .catch(e => console.error(`could not read a message from ${account}:`, e))
    .finally(() => {
      reading.set(account, reading.get(account) - 1)
      arm(account)
    })
  chains.set(account, done)
}

// The phone number the chat belongs to, as the core's account id. WhatsApp may address a chat by a
// LID (a private id) instead; the number usually comes with it or is in the session's LID mapping.
async function accountOf(key) {
  const ids = [key.remoteJid, key.remoteJidAlt].filter(Boolean)
  const pn = ids.find(isPnUser)
  if (pn) return `+${jidDecode(pn).user}`
  const lid = ids.find(isLidUser)
  if (!lid) return null
  const mapped = await sock.signalRepository.lidMapping.getPNForLID(lid).catch(() => null)
  return mapped ? `+${jidDecode(mapped).user}` : jidNormalizedUser(lid)
}

// A function that turns the message into texts for the agent, or null to ignore the message.
function reader(content, m) {
  if (!content) return null
  switch (getContentType(content)) {
    case 'conversation':
      return async () => [content.conversation]
    case 'extendedTextMessage':
      return async () => [content.extendedTextMessage.text]
    case 'audioMessage':
      return async () => [await upload(m, content.audioMessage.mimetype, 'voice note')]
    case 'imageMessage':
      return async () => [await upload(m, content.imageMessage.mimetype, 'photo'), content.imageMessage.caption]
    case 'documentMessage': {
      const { mimetype, caption, fileName } = content.documentMessage
      if (!/^(application\/pdf|image\/(jpeg|png|webp))/.test(mimetype ?? '')) {
        return async () => [`[file ${fileName ?? ''} — can't be opened: only photos and PDFs]`, caption]
      }
      return async () => [await upload(m, mimetype, 'document'), caption]
    }
    case 'locationMessage':
    case 'liveLocationMessage': {
      const { name, address, degreesLatitude: lat, degreesLongitude: lon } = content.locationMessage ?? content.liveLocationMessage
      return async () => [`[location: ${[name, address].filter(Boolean).join(', ') || `${lat?.toFixed(5)}, ${lon?.toFixed(5)}`}]`]
    }
    case 'videoMessage':
    case 'ptvMessage':
      return async () => ['[video — can\'t be opened: only voice notes, photos and PDFs]', content.videoMessage?.caption]
    case 'contactMessage':
    case 'contactsArrayMessage':
      return async () => ['[contact card — can\'t be opened]']
    default:
      return null
  }
}

async function upload(m, mimetype, kind) {
  try {
    const data = await downloadMediaMessage(m, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage })
    const form = new FormData()
    form.append('file', new Blob([data], { type: mimetype ?? 'application/octet-stream' }), kind.replace(' ', '-'))
    const response = await fetch(`${CORE_URL}/agent/media`, {
      method: 'POST', headers: { Authorization: `Bearer ${CLIENT_TOKEN}` }, body: form,
    })
    if (!response.ok) throw new Error(`core answered ${response.status}: ${await response.text()}`)
    return (await response.json()).message
  } catch (e) {
    console.error(`could not read a ${kind}:`, e.message ?? e)
    return `[${kind} — could not be read]`
  }
}

// --- Debounce and the agent API ---

function arm(account) {
  clearTimeout(timers.get(account))
  timers.set(account, setTimeout(() => flush(account), DEBOUNCE))
}

async function flush(account) {
  timers.delete(account)
  if (reading.get(account)) return // a voice note or photo is still being read; it re-arms the timer
  const texts = pending.get(account)
  pending.delete(account)
  if (!texts?.length) return stopTyping(account)
  try {
    if (!CLIENT_TOKEN) throw new Error('CLIENT_TOKEN is missing: run `uv run h4h client token wa`')
    const response = await fetch(`${CORE_URL}/agent/messages`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${CLIENT_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id: account, messages: texts }),
    })
    if (!response.ok) throw new Error(`core answered ${response.status}: ${await response.text()}`)
    console.log(`${account}: ${texts.length} message(s) to the agent`)
  } catch (e) {
    console.error(`could not pass messages from ${account} to the core:`, e.message ?? e)
    stopTyping(account)
    await deliver(jids.get(account), SORRY)
  }
}

// --- Replies from the core ---

async function reply(request, response) {
  const token = (request.headers.authorization ?? '').replace(/^Bearer /, '')
  try {
    const { payload } = await jwtVerify(token, jwks, { audience: AUDIENCE, issuer: ISSUER, algorithms: ['EdDSA'] })
    if (payload.typ !== 'reply') throw new Error('expected a reply token')
  } catch (e) {
    return send(response, 401, { detail: `invalid reply token: ${e.message}` })
  }
  const { account_id: account, text } = JSON.parse(await body(request))
  if (!account || !text) return send(response, 422, { detail: 'account_id and text are required' })
  const jid = jids.get(account) ?? jidOf(account)
  stopTyping(account)
  if (linked) await deliver(jid, text)
  else outbox.push({ jid, text })
  send(response, 200, { ok: true })
}

function jidOf(account) {
  return account.endsWith('@lid') ? account : `${account.replace(/\D/g, '')}@s.whatsapp.net`
}

async function deliver(jid, text) {
  if (!jid) return
  try {
    await sock.sendMessage(jid, { text: whatsappFormat(text) })
  } catch (e) {
    console.error(`could not send to ${jid}:`, e.message ?? e)
  }
}

// WhatsApp's own markup: *bold*, _italic_, no headings, bare links.
function whatsappFormat(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '*$1*')
    .replace(/__(.+?)__/g, '_$1_')
    .replace(/^#{1,6}\s+(.+)$/gm, '*$1*')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '$1: $2')
}

function startTyping(account) {
  if (typing.has(account)) return
  const jid = jids.get(account)
  const started = Date.now()
  const tick = () => {
    if (Date.now() - started > TYPING_FOR) return stopTyping(account)
    sock.sendPresenceUpdate('composing', jid).catch(() => {})
  }
  tick()
  typing.set(account, setInterval(tick, 8000)) // WhatsApp drops "typing…" after about 10s
}

function stopTyping(account) {
  clearInterval(typing.get(account))
  if (typing.delete(account)) sock.sendPresenceUpdate('paused', jids.get(account)).catch(() => {})
}

// --- HTTP ---

function body(request) {
  return new Promise((resolve, reject) => {
    const chunks = []
    request.on('data', c => chunks.push(c)).on('end', () => resolve(Buffer.concat(chunks).toString())).on('error', reject)
  })
}

function send(response, status, json) {
  response.writeHead(status, { 'Content-Type': 'application/json' }).end(JSON.stringify(json))
}

async function statusPage(response) {
  const state = linked
    ? `<p class="ok">Linked to <b>${linked}</b>. Wasel is answering on WhatsApp.</p>`
    : qr
      ? `<p>On the phone with Wasel's number: WhatsApp &rsaquo; Settings &rsaquo; Linked devices &rsaquo; Link a device, then scan:</p>${await QRCode.toString(qr, { type: 'svg', margin: 2, width: 300 })}`
      : '<p>Connecting to WhatsApp…</p>'
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }).end(`<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wasel · WhatsApp</title>${linked ? '' : '<meta http-equiv="refresh" content="3">'}
<style>body{font:16px system-ui,sans-serif;max-width:420px;margin:48px auto;padding:0 16px;color:#111b21;background:#fff}
h1{font-size:20px}.ok{color:#008069}svg{display:block;margin:16px 0}</style></head>
<body><h1>Wasel · WhatsApp client</h1>${state}</body></html>`)
}

createServer((request, response) => {
  const path = new URL(request.url, 'http://x').pathname
  const route = request.method === 'POST' && path === '/messages' ? reply(request, response)
    : request.method === 'GET' && path === '/' ? statusPage(response)
      : Promise.resolve(send(response, 404, { detail: 'not found' }))
  route.catch(e => {
    console.error(e)
    if (!response.headersSent) send(response, 500, { detail: 'internal error' })
  })
}).listen(PORT, () => console.log(`WhatsApp client on http://localhost:${PORT}`))

if (!CLIENT_TOKEN) console.warn('CLIENT_TOKEN is missing: run `uv run h4h client token wa` from the repo root.')
connect().catch(e => {
  console.error('could not start WhatsApp:', e)
  process.exit(1)
})
