"""Text normalization for matching names (drugs, areas) and claims in Arabic and English."""

import re
from collections.abc import Iterable

from rapidfuzz import fuzz, process

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


_WORDS = re.compile(r"\w+")
_ARTICLES = ("وال", "بال", "ال")
# Words that don't change what a claim says, after normalize(). Every claim is about the ministry.
_FILLER = {
    "في", "من", "علي", "عن", "مع", "الي", "ان", "انو", "انه", "هل", "و", "او", "التي", "الذي", "هذا", "هذه", "هيدا", "هيدي",
    "وزاره", "صحه", "عامه", "ministry", "moph", "health", "public",
    "the", "a", "an", "is", "are", "of", "to", "in", "on", "for", "and", "or", "that", "this", "it", "now",
}
# "covers" and "doesn't cover" are opposite claims, however close their words.
_NEGATIONS = {"لا", "لم", "لن", "ما", "مش", "مو", "ليس", "ليست", "not", "no", "never", "doesn", "don", "isn", "won"}
SAME_CLAIM = 85  # rapidfuzz token_set_ratio between two keys from which they are one claim


def _stem(word: str) -> str:
    for article in _ARTICLES:
        if word.startswith(article) and len(word) > len(article) + 2:
            return word[len(article):]
    return word


def _negated(key: str) -> bool:
    return not _NEGATIONS.isdisjoint(key.split())


def claim_key(claim: str, known: Iterable[str] = ()) -> str:
    """The key near-duplicate claims share: their words in any order, ignoring case, Arabic letter
    variants, the article ال, punctuation and filler words. A claim close to a known key takes it."""
    words = {_stem(w) for w in _WORDS.findall(normalize(claim))} - _FILLER
    key = " ".join(sorted(words)) or normalize(claim).strip()
    alike = [k for k in known if _negated(k) == _negated(key)]
    match = process.extractOne(key, alike, scorer=fuzz.token_set_ratio, score_cutoff=SAME_CLAIM)
    return match[0] if match else key
