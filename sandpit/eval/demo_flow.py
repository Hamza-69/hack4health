"""Rehearse the demo story end to end through the web chat client, as a fresh user.

    uv run python -m sandpit.eval.demo_flow [--lang en|lb]

Needs `uv run h4h dev` running. Sends each user turn to the web client (as the browser would),
prints Wasel's replies as they arrive over the event stream, then approves the new request from
the ministry inbox's API (as the desk would) and waits for Wasel to tell the user.
Photos are stand-ins: an image url plus the one-line description the WhatsApp client would add.
"""

import argparse
import asyncio
import json
import time
import uuid

import httpx
from sqlalchemy import select

from core import db, tokens
from core.models import Admin

WEB = "http://localhost:9000"
REQUESTS = "http://localhost:8003/api"
QUIET = 8  # seconds without a reply that end a turn
TURN_TIMEOUT = 120


def photo(text: str, description: str) -> str:
    return f"[photo https://placehold.co/600x800/png?text={text}] {description}"


TURNS = {
    "en": [
        "My dad needs a hernia operation, does the ministry cover it?",
        "He's Lebanese and he has no insurance at all, no NSSF, nothing.",
        "Yes please, do it for us",
        photo("Medical+report", "Medical report from Dr. Karim Saad, Rafik Hariri University Hospital: patient Ali Haddad "
              "needs inguinal hernia repair, admission 2026-10-14, 'at the expense of the Ministry of Health', stamped and signed"),
        photo("NSSF+statement", "NSSF statement dated 2026-10-05: Ali Haddad is not covered by NSSF"),
        "His name is Ali Haddad, the operation is at Rafik Hariri University Hospital, I'm his son. He has no other cover.",
    ],
    "lb": [
        "بيي بدو يعمل عملية فتق، الوزارة بتغطيها؟",
        "هو لبناني وما معو ولا ضمان ولا تأمين",
        "إيه بليز قدملنا ياها",
        photo("Medical+report", "Medical report from Dr. Karim Saad, Rafik Hariri University Hospital: patient Ali Haddad "
              "needs inguinal hernia repair, admission 2026-10-14, 'at the expense of the Ministry of Health', stamped and signed"),
        photo("NSSF+statement", "NSSF statement dated 2026-10-05: Ali Haddad is not covered by NSSF"),
        "اسمو علي حداد، العملية بمستشفى رفيق الحريري الجامعي، وأنا ابنو. ما عندو أي جهة ضامنة تانية.",
    ],
}
MISSING_DOC = photo("Ikhraj+qaid", "Individual civil registry extract (ikhraj qaid fardi) of Ali Haddad, with his photo")
CONFIRM = {"en": "Yes, submit it", "lb": "إيه قدّمو"}
THANKS = {"en": "Great, thank you!", "lb": "تمام، يسلمو!"}


class Chat:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http
        self.account = str(uuid.uuid4())
        self.replies: asyncio.Queue[str] = asyncio.Queue()

    async def listen(self) -> None:
        async with self.http.stream("GET", f"{WEB}/api/events", params={"account_id": self.account}, timeout=None) as r:
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    event = json.loads(line[5:])
                    if event.get("type") in ("reply", "error"):
                        await self.replies.put(f"[{event['type']}] {event['text']}" if event["type"] == "error" else event["text"])

    async def wait(self) -> list[str]:
        got, start = [], time.monotonic()
        while time.monotonic() - start < TURN_TIMEOUT:
            try:
                got.append(await asyncio.wait_for(self.replies.get(), QUIET if got else TURN_TIMEOUT))
                print(f"  Wasel ({time.monotonic() - start:.1f}s): {got[-1]}\n")
            except TimeoutError:
                break
        return got

    async def say(self, text: str) -> list[str]:
        print(f"USER: {text}")
        await self.http.post(f"{WEB}/api/send", json={"account_id": self.account, "text": text})
        return await self.wait()


async def admin_token() -> str:
    async with db.Session() as session:
        admin = await session.scalar(select(Admin).limit(1))
    if admin is None:
        raise SystemExit("no admin: run `uv run h4h admin create <email>`")
    return tokens.admin_token(admin.id, admin.email, admin.role.value, "requests")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=TURNS, default="en")
    args = parser.parse_args()
    async with httpx.AsyncClient(timeout=30) as http:
        chat = Chat(http)
        listener = asyncio.create_task(chat.listen())
        await asyncio.sleep(0.5)
        for turn in TURNS[args.lang]:
            await chat.say(turn)
        await chat.say(MISSING_DOC)
        await chat.say(CONFIRM[args.lang])

        auth = {"Authorization": f"Bearer {await admin_token()}"}
        mine = [r for r in (await http.get(f"{REQUESTS}/requests", headers=auth)).json() if r["status"] == "submitted"]
        if not mine:
            print("!! no submitted request in the inbox")
        else:
            code, number = mine[0]["code"], mine[0]["number"]
            print(f"DESK: approves {code}")
            r = await http.post(f"{REQUESTS}/requests/{number}/approve", headers=auth,
                                json={"message": "Approval card ready at the hospital admissions office."})
            r.raise_for_status()
            await chat.wait()
            await chat.say(THANKS[args.lang])
        listener.cancel()


if __name__ == "__main__":
    asyncio.run(main())
