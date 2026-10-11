import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage, HumanMessage

from core import agent, media, tokens
from core.app import app

JPEG = b"\xff\xd8\xff\xe0fake jpeg"


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "MEDIA_DIR", tmp_path)

    async def transcribe(data, extension):
        return f"transcript of {len(data)} bytes of {extension}"

    async def describe(data, content_type):
        return "Lebanese ID card (بطاقة هوية), Ahmad Khalil"

    monkeypatch.setattr(media, "transcribe", transcribe)
    monkeypatch.setattr(media, "describe", describe)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def upload(client, data, content_type, token=None):
    headers = {"Authorization": f"Bearer {token or tokens.client_token('wa')}"}
    return await client.post("/agent/media", headers=headers, files={"file": ("upload", data, content_type)})


async def test_voice_note_becomes_a_transcript_and_is_not_kept(client, tmp_path):
    response = await upload(client, b"opus", "audio/ogg; codecs=opus")
    assert response.json() == {"message": "[voice note] transcript of 4 bytes of ogg"}
    assert not any(tmp_path.iterdir())


async def test_photo_is_kept_behind_a_random_link_and_described(client):
    message = (await upload(client, JPEG, "image/jpeg")).json()["message"]
    tag, description = message.split("] ", 1)
    link = tag.removeprefix("[photo ")
    assert description == "Lebanese ID card (بطاقة هوية), Ahmad Khalil"
    assert link.startswith(f"{media.PUBLIC_URL}/media/") and link.endswith(".jpg")
    served = await client.get(link.removeprefix(media.PUBLIC_URL))
    assert served.status_code == 200 and served.content == JPEG


@pytest.mark.parametrize("name", ["missing0000000000000000.jpg", "..%2Fkeys%2Fprivate.pem", "short.jpg", "x" * 22 + ".py"])
async def test_only_stored_media_is_served(client, name):
    assert (await client.get(f"/media/{name}")).status_code == 404


async def test_unusable_uploads_are_refused(client):
    assert (await upload(client, b"MZ", "application/x-msdownload")).status_code == 415
    assert (await upload(client, b"", "image/jpeg")).status_code == 422


async def test_only_registered_clients_can_upload(client):
    assert (await upload(client, JPEG, "image/jpeg", token=tokens.module_token("testmod"))).status_code == 401
    assert (await upload(client, JPEG, "image/jpeg", token=tokens.client_token("tg"))).status_code == 401


@pytest.fixture
def classified(monkeypatch):
    """Stands in for gpt-6-luna: Arabizi when the last message has "baddi" or "lezem"; records what it was asked."""
    asked = []

    async def classify(texts):
        asked.append(texts)
        return "arabizi" if any(w in texts[0] for w in ("baddi", "lezem")) else "latin"

    monkeypatch.setattr(agent, "_classify", classify)
    monkeypatch.setattr(agent, "_scripts", {})
    return asked


async def script(*messages):
    return await agent._script(agent._user_texts(list(messages)))


async def test_language_ignores_links_and_media_descriptions(classified):
    photo = HumanMessage("[photo http://localhost:8000/media/k6kAb3dE9fGh2jKl4mNp7q.jpg] a prescription")
    assert await script(HumanMessage("Which hospitals are in Zahle?"), photo) == "latin"
    arabic_doc = HumanMessage("[photo http://x/a.jpg] civil registry extract (إخراج قيد فردي)")
    assert await script(HumanMessage("Yes please, do it for us"), arabic_doc) == "latin"
    assert classified == [("Which hospitals are in Zahle?",), ("Yes please, do it for us",)]


async def test_language_follows_the_user_through_voice_notes_and_supplier_updates(classified):
    supplier = HumanMessage("[supplier · requests · ticket 1] Approved")
    assert await script(HumanMessage("kifak, baddi 3melye"), AIMessage("..."), supplier) == "arabizi"
    assert await script(HumanMessage("[voice note] shou lezem jib ma3e?")) == "arabizi"
    assert await script(HumanMessage("[voice note] شو لازم جيب معي؟")) == "arabic"
    assert len(classified) == 2  # Arabic script needs no model


async def test_short_replies_are_classified_with_earlier_messages_once_per_turn(classified):
    chat = [HumanMessage("baddi 3melye"), AIMessage("..."), HumanMessage("merci")]
    assert await script(*chat) == "latin"
    assert await script(*chat) == "latin"
    assert classified == [("merci", "baddi 3melye")]


async def test_no_language_hint_when_the_classifier_fails(monkeypatch):
    async def fail(texts):
        raise TimeoutError

    monkeypatch.setattr(agent, "_classify", fail)
    monkeypatch.setattr(agent, "_scripts", {})
    assert await script(HumanMessage("eh hydi sah")) is None


def test_wrong_script_ignores_links_and_bracketed_names():
    english = "Send a photo of the civil registry extract (إخراج قيد فردي): https://www.moph.gov.lb/ar/x"
    assert not agent._wrong_script("latin", english)
    assert agent._wrong_script("latin", "أكيد. فيني حضّر الطلب، بس بحتاج منك تبعتلي صور هالمستندات")
    assert agent._wrong_script("arabic", "Sure, send me the medical report and the NSSF statement")
    assert agent._wrong_script("arabizi", "Eh, lezem ikhraj qaid (إخراج قيد)")


def test_reading_is_one_line_of_fields_kind_first():
    reading = media.Reading(
        kind="civil registry extract", title_ar="إخراج قيد فردي", name="Ali Haddad", issuer="Department of Civil Status",
        issued="2026-10-08", expires=None,
        details=[media.Detail(label="Father", value="Mahmoud"), media.Detail(label="date of birth", value="1961-03-14")],
        readable=True, problems=None,
    )
    assert reading.line() == (
        "civil registry extract (إخراج قيد فردي) | name: Ali Haddad | issued by: Department of Civil Status | "
        "issued: 2026-10-08 | father: Mahmoud | date of birth: 1961-03-14"
    )
    blurry = reading.model_copy(update={"readable": False, "problems": "cut off at the bottom", "details": []})
    assert blurry.line().endswith("| hard to read: cut off at the bottom")
