"""Start the demo from a clean slate: no chats, tickets or requests, and W-1042 is the next number.

    uv run python -m sandpit.demo.reset

Clears every user (and so every chat), ticket and archive, the requests module's requests, and the
moph module's search log and unanswered questions. Keeps admins, the ministry data and the search index.
The web chat keeps its browser id: press "New chat" there too.
"""

import asyncio

from sqlalchemy import text

from core.db import engine

FIRST_NUMBER = 1042  # modules/requests/app/models.py

STATEMENTS = [
    "TRUNCATE users, tickets, archives CASCADE",
    "TRUNCATE requests.requests",
    f"ALTER SEQUENCE requests.request_number_seq RESTART WITH {FIRST_NUMBER}",
    "TRUNCATE moph.search_log, moph.gaps",
]


async def main() -> None:
    async with engine.begin() as conn:
        for statement in STATEMENTS:
            await conn.execute(text(statement))
    print(f"Clean slate: no chats, tickets or requests; the next request is W-{FIRST_NUMBER}.")


if __name__ == "__main__":
    asyncio.run(main())
