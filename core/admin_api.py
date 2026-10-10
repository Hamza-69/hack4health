"""API for the admin panel shell. Authenticated with the admin's session token."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from core import tokens
from core.auth import DB, CurrentAdmin
from core.models import Admin, Ticket, TicketStatus
from core.passwords import verify_password
from core.registry import load_modules
from core.schemas import AdminOut, AdminTicketOut, LoginIn, LoginOut, ModuleOut, TokenOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
async def login(body: LoginIn, session: DB) -> LoginOut:
    admin = await session.scalar(select(Admin).where(Admin.email == body.email.lower()))
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(401, "wrong email or password")
    return LoginOut(token=tokens.session_token(admin.id), admin=AdminOut.model_validate(admin))


@router.get("/me")
async def me(admin: CurrentAdmin) -> AdminOut:
    return AdminOut.model_validate(admin)


@router.get("/modules")
async def modules(admin: CurrentAdmin) -> list[ModuleOut]:
    return [
        ModuleOut(name=m.name, title=m.title, ui_url=m.ui_url)
        for m in load_modules().values()
        if admin.can_open(m.name)
    ]


@router.post("/modules/{name}/token")
async def module_token(name: str, admin: CurrentAdmin) -> TokenOut:
    """Admin token for one module's UI. The shell passes it into the module's iframe."""
    if name not in load_modules():
        raise HTTPException(404, f"no module {name!r}")
    if not admin.can_open(name):
        raise HTTPException(403, f"no access to {name!r}")
    return TokenOut(token=tokens.admin_token(admin.id, admin.email, admin.role, name))


@router.get("/tickets")
async def tickets(
    admin: CurrentAdmin, session: DB, status: TicketStatus | None = None, kind: str | None = None
) -> list[AdminTicketOut]:
    query = select(Ticket).order_by(Ticket.created_at.desc()).limit(500)
    if status:
        query = query.where(Ticket.status == status)
    if kind:
        query = query.where(Ticket.kind == kind)
    rows = await session.scalars(query)
    return [AdminTicketOut.model_validate(t) for t in rows if admin.can_open(t.kind)]
