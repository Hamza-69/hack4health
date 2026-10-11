/* Wasel on any website. One tag adds the chat button and panel:

     <script src="https://<wasel host>/widget.js" defer></script>

   Options, as data- attributes on that tag:
     data-lang="ar|en"          the chat's language (default: the page's <html lang>)
     data-position="left|right" the corner (default: right, or left on right-to-left pages)
     data-open="true"           start with the chat open
     data-ns="ministry"         keep this page's conversation apart from the others in the browser
                                (the demo pages use it; a real site leaves it out)

   From the page's own scripts:
     Wasel.open(), Wasel.close(), Wasel.toggle()
     Wasel.ask("How do I apply for IVIG?")  opens the chat and sends the question, e.g. from a
                                            "Ask Wasel about this service" button on a service page

   Everything renders in a shadow root, so the site's styles and the widget's never touch. The chat
   itself (an iframe of /chat) loads on the first open, so the widget costs the page almost nothing. */
(() => {
  if (window.Wasel) return;
  const script = document.currentScript || document.querySelector('script[src*="widget.js"]');
  if (!script) return;

  const base = new URL(".", script.src);
  const data = script.dataset;
  const pageLang = (document.documentElement.lang || navigator.language || "").slice(0, 2).toLowerCase();
  const lang = ["ar", "en"].includes(data.lang) ? data.lang : pageLang === "ar" ? "ar" : "en";
  const pageRtl = getComputedStyle(document.documentElement).direction === "rtl";
  const side = ["left", "right"].includes(data.position) ? data.position : pageRtl ? "left" : "right";
  const chatUrl = new URL("chat", base);
  chatUrl.search = new URLSearchParams({ embed: "widget", lang, ...(data.ns ? { ns: data.ns } : {}) });

  const TEXT = {
    en: { open: "Ask Wasel", close: "Close the chat", title: "Wasel, the Ministry of Public Health assistant",
          teaser: "Questions about ministry services? Ask Wasel.", dismiss: "Dismiss" },
    ar: { open: "اسأل واصل", close: "سكّر المحادثة", title: "واصل، مساعد وزارة الصحة العامة",
          teaser: "عندك سؤال عن خدمات الوزارة؟ اسأل واصل.", dismiss: "إخفاء" },
  }[lang];

  const MARK = '<svg viewBox="84 84 334 354" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="M300 92C362 92 410 142 410 210C410 322 318 410 116 428C96 430 92 410 110 404C214 372 262 340 280 318C226 310 190 266 190 208C190 144 238 92 300 92ZM292 150C315 150 332 168 332 192C332 216 315 234 292 234C269 234 252 216 252 192C252 168 269 150 292 150Z"/></svg>';
  const CLOSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';

  const host = document.createElement("div");
  host.id = "wasel-widget";
  // Above the site's own layers; a third-party widget can't know their z-index scale.
  host.style.cssText = "position:fixed;z-index:2147483000;inset:auto;";
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `
    <style>
      :host { all: initial; }
      * { box-sizing: border-box; }
      .wrap { position: fixed; bottom: 20px; ${side}: 20px; display: flex; flex-direction: column;
              align-items: ${side === "right" ? "flex-end" : "flex-start"}; gap: 12px;
              font: 14px/1.4 system-ui, -apple-system, "Segoe UI", "Noto Sans Arabic", "Geeza Pro", sans-serif; }
      .launcher { position: relative; width: 60px; height: 60px; border-radius: 50%; border: 0; cursor: pointer; padding: 0;
                  display: grid; place-items: center; color: #f4ecdc; background: #0d5c48;
                  box-shadow: 0 6px 18px rgb(13 92 72 / 0.32), 0 1px 3px rgb(0 0 0 / 0.12);
                  transition: transform 160ms cubic-bezier(0.2, 0.7, 0.2, 1), background-color 160ms; }
      .launcher:hover { background: #0b4f3e; }
      .launcher:active { transform: scale(0.95); }
      .launcher:focus-visible, .teaser button:focus-visible { outline: 3px solid #f2b84b; outline-offset: 3px; }
      .launcher svg { width: 30px; height: 30px; }
      .launcher .x { display: none; width: 24px; height: 24px; }
      .open .launcher .mark { display: none; }
      .open .launcher .x { display: block; }
      .badge { position: absolute; top: 2px; ${side === "right" ? "right" : "left"}: 2px; width: 14px; height: 14px; border-radius: 50%;
               background: #e5484d; border: 2px solid #fff; display: none; }
      .unread .badge { display: block; }
      .teaser { display: none; max-width: 260px; padding: 12px 14px; border-radius: 14px; background: #fff; color: #17201c;
                box-shadow: 0 8px 24px rgb(0 0 0 / 0.14); cursor: pointer; position: relative; animation: rise 220ms cubic-bezier(0.2, 0.7, 0.2, 1); }
      .teaser.show { display: block; }
      .teaser p { margin: 0; padding-${side === "right" ? "right" : "left"}: 18px; }
      .teaser button { position: absolute; top: 6px; ${side === "right" ? "right" : "left"}: 6px; width: 22px; height: 22px; border: 0;
                       border-radius: 50%; background: none; color: #66726c; cursor: pointer; display: grid; place-items: center; padding: 0; }
      .teaser button svg { width: 14px; height: 14px; }
      .panel { width: 400px; height: min(680px, calc(100vh - 116px)); border-radius: 18px; overflow: hidden; background: #fbfaf6;
               box-shadow: 0 16px 48px rgb(0 0 0 / 0.22), 0 2px 6px rgb(0 0 0 / 0.08);
               opacity: 0; transform: translateY(8px) scale(0.985); transform-origin: bottom ${side};
               visibility: hidden; transition: opacity 180ms cubic-bezier(0.2, 0.7, 0.2, 1), transform 180ms cubic-bezier(0.2, 0.7, 0.2, 1), visibility 0s 180ms; }
      .open .panel { opacity: 1; transform: none; visibility: visible; transition-delay: 0s; }
      iframe { width: 100%; height: 100%; border: 0; display: block; background: transparent; }
      @keyframes rise { from { opacity: 0; transform: translateY(6px); } }
      @media (max-width: 480px) {
        .wrap { bottom: 16px; ${side}: 16px; }
        .panel { position: fixed; inset: 0; width: 100%; height: 100%; border-radius: 0; }
        .open .launcher { display: none; }
      }
      @media (prefers-reduced-motion: reduce) {
        .panel, .open .panel { transform: none; transition: opacity 120ms linear, visibility 0s; }
        .teaser { animation: none; }
      }
    </style>
    <div class="wrap" dir="${lang === "ar" ? "rtl" : "ltr"}">
      <div class="panel" role="dialog" aria-label="${TEXT.title}" id="wasel-panel"></div>
      <div class="teaser" role="status"><p>${TEXT.teaser}</p><button type="button" aria-label="${TEXT.dismiss}">${CLOSE}</button></div>
      <button class="launcher" type="button" aria-label="${TEXT.open}" aria-expanded="false" aria-controls="wasel-panel">
        <span class="mark">${MARK}</span><span class="x">${CLOSE}</span><i class="badge"></i>
      </button>
    </div>`;

  const wrap = root.querySelector(".wrap");
  const panel = root.querySelector(".panel");
  const launcher = root.querySelector(".launcher");
  const teaser = root.querySelector(".teaser");
  let frame = null, ready = false, isOpen = false;
  const waiting = [];  // questions asked before the chat finished loading
  const session = {
    get(key) { try { return sessionStorage.getItem(key); } catch { return null; } },
    set(key) { try { sessionStorage.setItem(key, "1"); } catch {} },
  };

  function post(message) {
    if (frame && ready) frame.contentWindow.postMessage(message, chatUrl.origin);
    else waiting.push(message);
  }

  function load() {
    if (frame) return;
    frame = document.createElement("iframe");
    frame.title = TEXT.title;
    frame.src = chatUrl.href;
    frame.allow = "microphone; clipboard-write";
    panel.append(frame);
  }

  function open() {
    load();
    isOpen = true;
    session.set("wasel.opened");
    teaser.classList.remove("show");
    wrap.classList.add("open");
    wrap.classList.remove("unread");
    launcher.setAttribute("aria-expanded", "true");
    launcher.setAttribute("aria-label", TEXT.close);
    if (matchMedia("(max-width: 480px)").matches) document.documentElement.style.overflow = "hidden";
    post({ type: "wasel:focus" });
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    wrap.classList.remove("open");
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-label", TEXT.open);
    document.documentElement.style.overflow = "";
    launcher.focus({ preventScroll: true });
  }

  function ask(text) {
    if (typeof text !== "string" || !text.trim()) return open();
    open();
    post({ type: "wasel:ask", text: text.trim() });
  }

  launcher.addEventListener("click", () => (isOpen ? close() : open()));
  teaser.addEventListener("click", (e) => {
    teaser.classList.remove("show");
    session.set("wasel.teaser");
    if (!e.target.closest("button")) open();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && isOpen) close(); });

  window.addEventListener("message", (e) => {
    if (!frame || e.source !== frame.contentWindow || e.origin !== chatUrl.origin || !e.data) return;
    if (e.data.type === "wasel:ready") {
      ready = true;
      waiting.splice(0).forEach(post);
      if (isOpen) post({ type: "wasel:focus" });
    } else if (e.data.type === "wasel:close") {
      close();
    } else if (e.data.type === "wasel:reply" && !isOpen) {
      wrap.classList.add("unread");
    }
  });

  function mount() {
    document.body.append(host);
    if (data.open === "true") open();
    else if (!session.get("wasel.teaser") && !session.get("wasel.opened")) {
      setTimeout(() => { if (!isOpen) teaser.classList.add("show"); }, 4000);
    }
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);

  window.Wasel = { open, close, toggle: () => (isOpen ? close() : open()), ask };
})();
