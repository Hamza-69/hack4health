import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from core import tokens
from core.app import app
from core.auth import get_session
from core.models import Admin, AdminRole, User
from core.passwords import hash_password


@pytest.fixture
async def client(session):
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def login(client, session, role=AdminRole.OPERATOR, modules=()) -> dict:
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    session.add(Admin(email=email, password_hash=hash_password("pw"), role=role, modules=list(modules)))
    await session.commit()
    response = await client.post("/admin/login", json={"email": email, "password": "pw"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def as_module(name="testmod") -> dict:
    return {"Authorization": f"Bearer {tokens.module_token(name)}"}


async def test_wrong_password_is_rejected(client, session):
    await login(client, session)
    response = await client.post("/admin/login", json={"email": "nobody@example.com", "password": "pw"})
    assert response.status_code == 401


async def test_operator_sees_modules_and_gets_a_module_token(client, session):
    headers = await login(client, session)
    modules = (await client.get("/admin/modules", headers=headers)).json()
    assert modules == [{"name": "testmod", "title": "Testmod", "ui_url": "http://localhost:9999/ui/"}]
    response = await client.post("/admin/modules/testmod/token", headers=headers)
    assert response.status_code == 200


async def test_supplier_only_opens_their_modules(client, session):
    headers = await login(client, session, AdminRole.SUPPLIER, modules=["other"])
    assert (await client.get("/admin/modules", headers=headers)).json() == []
    assert (await client.post("/admin/modules/testmod/token", headers=headers)).status_code == 403


async def test_module_ticket_flow(client, session):
    user_id = uuid.uuid4()
    created = await client.post(
        "/module/tickets", headers=as_module(), json={"user_id": str(user_id), "title": "Refill"}
    )
    assert created.status_code == 200
    ticket = created.json()
    assert (ticket["kind"], ticket["status"]) == ("testmod", "active")

    notified = await client.post(
        f"/module/tickets/{ticket['id']}/notify", headers=as_module(), json={"message": "Ready Tue"}
    )
    assert notified.json()["status"] == "awaiting_user"
    user = await session.scalar(select(User).where(User.id == user_id).execution_options(populate_existing=True))
    assert user.messages[-1]["content"].endswith("Ready Tue")

    resolved = await client.patch(
        f"/module/tickets/{ticket['id']}", headers=as_module(), json={"status": "resolved", "resolution": "Picked up"}
    )
    assert (resolved.json()["status"], resolved.json()["resolution"]) == ("resolved", "Picked up")

    admin_view = (await client.get("/admin/tickets", headers=await login(client, session))).json()
    assert [t["id"] for t in admin_view] == [ticket["id"]]
    assert "user_id" not in admin_view[0]


async def test_module_only_sees_its_own_tickets(client, session):
    created = await client.post(
        "/module/tickets", headers=as_module(), json={"user_id": str(uuid.uuid4()), "title": "t"}
    )
    # A module removed from the registry loses access.
    response = await client.get(f"/module/tickets/{created.json()['id']}", headers=as_module("ghost"))
    assert response.status_code == 401
