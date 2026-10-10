import uuid
from datetime import datetime

import httpx
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel


class Ticket(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    title: str
    details: str | None
    status: str  # active | awaiting_user | resolved | archived
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None


class CoreError(ToolError):
    """The core API refused a request.

    In a tool, the message reaches the agent. In an API route, the client gets the same HTTP status.
    """

    def __init__(self, status_code: int, detail: str):
        super().__init__(f"core API {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class CoreClient:
    """The core's module API, authenticated with this module's MODULE_TOKEN."""

    def __init__(self, core_url: str, module_token: str | None):
        self._token = module_token
        self._http = httpx.AsyncClient(base_url=f"{core_url}/module", timeout=10)

    async def create_ticket(
        self, user_id: uuid.UUID, title: str, details: str | None = None
    ) -> Ticket:
        body = {"user_id": str(user_id), "title": title, "details": details}
        return Ticket.model_validate(await self._request("POST", "/tickets", json=body))

    async def get_ticket(self, ticket_id: uuid.UUID | str) -> Ticket:
        return Ticket.model_validate(await self._request("GET", f"/tickets/{ticket_id}"))

    async def list_tickets(self, status: str | None = None) -> list[Ticket]:
        params = {"status": status} if status else None
        rows = await self._request("GET", "/tickets", params=params)
        return [Ticket.model_validate(row) for row in rows]

    async def update_ticket(
        self,
        ticket_id: uuid.UUID | str,
        *,
        status: str | None = None,
        resolution: str | None = None,
    ) -> Ticket:
        body = {k: v for k, v in {"status": status, "resolution": resolution}.items() if v}
        return Ticket.model_validate(await self._request("PATCH", f"/tickets/{ticket_id}", json=body))

    async def notify(self, ticket_id: uuid.UUID | str, message: str) -> Ticket:
        """Tell the user about a supplier update. Moves the ticket to awaiting_user."""
        body = {"message": message}
        return Ticket.model_validate(
            await self._request("POST", f"/tickets/{ticket_id}/notify", json=body)
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str, **kwargs):
        if not self._token:
            raise CoreError(500, "MODULE_TOKEN is not set; run `uv run h4h module token <name>`")
        headers = {"Authorization": f"Bearer {self._token}"}
        response = await self._http.request(method, path, headers=headers, **kwargs)
        if response.is_error:
            raise CoreError(response.status_code, response.json().get("detail", response.text))
        return response.json()
