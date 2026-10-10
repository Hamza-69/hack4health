"""One user per app account. The user id is a uuid5 of the app-prefixed account id."""

import uuid
from typing import Literal

import phonenumbers

App = Literal["wa", "tg", "web"]

# Every user id is derived from this. Changing it orphans every existing user.
NAMESPACE = uuid.UUID("aae45951-5e3b-4bcd-b5c8-d81e3261328f")


def user_id_for(app: App, account_id: str) -> uuid.UUID:
    match app:
        case "wa":
            account_id = normalize_phone(account_id)
        case "tg":
            account_id = str(int(account_id))
        case "web":
            account_id = str(uuid.UUID(account_id))
    return uuid.uuid5(NAMESPACE, f"{app}:{account_id}")


def normalize_phone(raw: str) -> str:
    """Return the number in E.164 (+96170123456). WhatsApp sends numbers without the +."""
    raw = raw.strip()
    if not raw.startswith("+"):
        raw = "+" + raw.removeprefix("00")
    try:
        number = phonenumbers.parse(raw)
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"not a phone number: {raw!r}") from e
    if not phonenumbers.is_possible_number(number):
        raise ValueError(f"not a phone number: {raw!r}")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
