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


def test_arabizi_hint_ignores_links_and_media_descriptions():
    photo = HumanMessage("[photo http://localhost:8000/media/k6kAb3dE9fGh2jKl4mNp7q.jpg] a prescription")
    assert agent._script_hint([HumanMessage("Which hospitals are in Zahle?"), photo]) is None


def test_arabizi_hint_follows_the_user_through_voice_notes_and_supplier_updates():
    supplier = HumanMessage("[supplier · requests · ticket 1] Approved")
    assert agent._script_hint([HumanMessage("kifak, baddi 3melye"), AIMessage("..."), supplier])
    assert agent._script_hint([HumanMessage("[voice note] shou lezem jib ma3e?")])
    assert agent._script_hint([HumanMessage("[voice note] شو لازم جيب معي؟")]) is None
