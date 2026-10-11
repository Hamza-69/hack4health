"""Clear every request and restart numbering at W-1042, before a demo.

    cd modules/requests && uv run python -m app.reset

Core tickets are not touched; reset those from the core side.
"""

import asyncio

from sqlalchemy import delete, text

from app.models import FIRST_NUMBER, Request
from app.module import module


async def main() -> None:
    async with module.db() as session:
        await session.execute(delete(Request))
        await session.execute(text(f"ALTER SEQUENCE requests.request_number_seq RESTART WITH {FIRST_NUMBER}"))
        await session.commit()
    print(f"Requests cleared; the next one is W-{FIRST_NUMBER}.")


if __name__ == "__main__":
    asyncio.run(main())
