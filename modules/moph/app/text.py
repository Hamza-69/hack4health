"""Text normalization for matching names (drugs, areas) in Arabic and English."""

import re

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")  # incl. tatweel
_LETTERS = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
        **{chr(0x0660 + i): str(i) for i in range(10)},  # Arabic-Indic digits
        **{chr(0x06F0 + i): str(i) for i in range(10)},  # Persian digits
    }
)
_ARABIC = re.compile(r"[؀-ۿ]")


def normalize(text: str) -> str:
    """Lowercase, strip Arabic diacritics and tatweel, unify letter variants and digits."""
    return _DIACRITICS.sub("", text).translate(_LETTERS).lower()


def is_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text))
