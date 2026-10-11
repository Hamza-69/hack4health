"""Masking personal details in text a module keeps for its staff (questions, searches, rumours).

The chat itself never reaches staff; this is for what a module stores about what people ask. It
masks e-mails, numbers of 7 digits or more (phones, IDs, registry numbers) and the names people
introduce ("اسمو علي حداد", "my name is ...", "ismi ..."). It prefers masking too much to too little.
"""

import re

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Seven digits or more, allowing the separators people type in phone numbers: +961 70 123 456, 03/123456.
_NUMBER = re.compile(r"(?<![\w.])\+?\d(?:[\s\-/.]?\d){6,}(?!\w)")
_INTRO = (
    r"(?:[اإ]سم(?:ي|و|ه|ها)|my name is|his name is|her name is|i am called|"
    r"je m'appelle|il s'appelle|elle s'appelle|[ie]sm(?:i|o|ou|a))"
)
_STOP = r"(?:و|w|and|et|bas|بس)"
_NAME = re.compile(
    rf"(?i)(?<!\w)({_INTRO}\s+)((?!{_STOP}\b)[^\W\d_]+(?:\s+(?!{_STOP}\b)[^\W\d_]+)?)"
)


def mask_personal(text: str) -> str:
    """The text with personal details replaced by [email], [number] and [name]."""
    if not text:
        return text
    text = _EMAIL.sub("[email]", text.translate(_DIGITS))
    text = _NUMBER.sub("[number]", text)
    return _NAME.sub(lambda m: m.group(1) + "[name]", text)
