"""Media from chat clients, turned into messages the agent reads like any other:

    [voice note] <transcript>
    [photo <link>] <one line on what it shows>
    [document <link>] <one line on what it is>

Voice notes are transcribed and not kept. Photos and PDFs are kept in MEDIA_DIR and served at
/media/<name>. The name is random, so only whoever holds the link can open the file: the agent,
and a module it hands the link to (the ministry desk reviewing a request).
"""

import base64
import os
import re
import secrets
from functools import cache
from pathlib import Path

from openai import AsyncOpenAI

MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", "media"))
PUBLIC_URL = os.environ.get("CORE_PUBLIC_URL", "http://localhost:8000").rstrip("/")  # where links point
TRANSCRIBE_MODEL = os.environ.get("TRANSCRIBE_MODEL", "gpt-4o-transcribe")
VISION_MODEL = os.environ.get("VISION_MODEL", "gpt-5.4-mini")
MAX_BYTES = 20 * 1024 * 1024
TIMEOUT = 60  # seconds per OpenAI call

# Extensions OpenAI recognises; it picks the audio format from the file name.
AUDIO = {"audio/ogg": "ogg", "audio/opus": "ogg", "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/x-m4a": "m4a",
         "audio/aac": "m4a", "audio/webm": "webm", "audio/wav": "wav", "audio/x-wav": "wav"}
IMAGES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
DOCUMENTS = {"application/pdf": "pdf"}
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{22}\.(jpg|png|webp|pdf)$")

TRANSCRIBE_PROMPT = (
    "A patient in Lebanon asking about Ministry of Public Health services, hospitals or medicines. "
    "Lebanese Arabic, often mixed with English or French words."
)
DESCRIBE_PROMPT = """\
A patient sent this to the Lebanese Ministry of Public Health's assistant, usually as part of a \
request. Say in one line (at most 35 words) what it is.
- A document: its type in English, judged from what is printed on it, not from who it is being sent \
to, then the Arabic title if one is printed (e.g. "Lebanese ID card \
(بطاقة هوية)", "civil registry extract (إخراج قيد فردي)", "medical report (تقرير طبي)", "NSSF \
statement (إفادة الضمان)", "prescription"), whose it is if a name is printed, its issue date if one \
is printed (not a date of birth), and whether it is stamped or signed. Say if it is unreadable, cut \
off or blurry.
- Anything else: what it shows, plainly, with no medical judgement.
Write only the line."""


class MediaError(ValueError):
    """The upload can't be used: wrong type, too big, or empty. `status` is the HTTP status to answer with."""

    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def kind_of(content_type: str) -> str:
    base = content_type.split(";")[0].strip().lower()
    if base in AUDIO:
        return "voice"
    if base in IMAGES:
        return "photo"
    if base in DOCUMENTS:
        return "document"
    raise MediaError(f"unsupported media type {base!r}: send a voice note, a JPEG/PNG/WebP photo or a PDF", 415)


async def to_message(data: bytes, content_type: str) -> str:
    """The message for one upload. Raises MediaError for unusable uploads."""
    if not data:
        raise MediaError("empty file")
    if len(data) > MAX_BYTES:
        raise MediaError(f"file is over {MAX_BYTES // (1024 * 1024)} MB", 413)
    base = content_type.split(";")[0].strip().lower()
    match kind_of(base):
        case "voice":
            text = await transcribe(data, AUDIO[base])
            return f"[voice note] {text or '(no speech could be made out)'}"
        case "photo":
            link = save(data, IMAGES[base])
            return f"[photo {link}] {await describe(data, base)}"
        case _:
            link = save(data, DOCUMENTS[base])
            return f"[document {link}] {await describe(data, base)}"


def save(data: bytes, extension: str) -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_urlsafe(16)}.{extension}"
    (MEDIA_DIR / name).write_bytes(data)
    return f"{PUBLIC_URL}/media/{name}"


def path(name: str) -> Path | None:
    """The stored file for a /media/<name> link, or None."""
    if not NAME_RE.match(name):
        return None
    file = MEDIA_DIR / name
    return file if file.is_file() else None


@cache
def _openai() -> AsyncOpenAI:
    return AsyncOpenAI(timeout=TIMEOUT, max_retries=2)


async def transcribe(data: bytes, extension: str) -> str:
    result = await _openai().audio.transcriptions.create(
        model=TRANSCRIBE_MODEL, file=(f"voice.{extension}", data), prompt=TRANSCRIBE_PROMPT
    )
    return result.text.strip()


async def describe(data: bytes, content_type: str) -> str:
    url = f"data:{content_type};base64,{base64.b64encode(data).decode()}"
    part = (
        {"type": "input_file", "filename": "document.pdf", "file_data": url}
        if content_type in DOCUMENTS
        else {"type": "input_image", "image_url": url, "detail": "high"}
    )
    response = await _openai().responses.create(
        model=VISION_MODEL,
        input=[{"role": "user", "content": [{"type": "input_text", "text": DESCRIBE_PROMPT}, part]}],
    )
    return " ".join(response.output_text.split()) or "(could not tell what this is)"
