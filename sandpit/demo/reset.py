"""Start the demo from a clean slate: no chats, tickets, requests or reports; W-1042 and R-501 are next.

    uv run python -m sandpit.demo.reset

Clears every user (and so every chat), ticket and archive, the requests module's requests, the bills
module's reports, and the moph module's search log, unanswered questions and checked rumours. Keeps admins, the ministry data and the search index.
The web chat keeps its browser id: press "New chat" there too.
"""

import asyncio

from sqlalchemy import text

from core.db import engine

FIRST_NUMBER = 1042  # modules/requests/app/models.py
FIRST_REPORT = 501  # modules/bills/app/models.py

STATEMENTS = [
    "TRUNCATE users, tickets, archives CASCADE",
    "TRUNCATE requests.requests",
    f"ALTER SEQUENCE requests.request_number_seq RESTART WITH {FIRST_NUMBER}",
    "TRUNCATE bills.reports",
    f"ALTER SEQUENCE bills.report_number_seq RESTART WITH {FIRST_REPORT}",
    "TRUNCATE moph.search_log, moph.gaps, moph.claims",
]


async def main() -> None:
    async with engine.begin() as conn:
        for statement in STATEMENTS:
            await conn.execute(text(statement))
    print(f"Clean slate: no chats, tickets, requests or reports; next are W-{FIRST_NUMBER} and R-{FIRST_REPORT}.")


if __name__ == "__main__":
    asyncio.run(main())
