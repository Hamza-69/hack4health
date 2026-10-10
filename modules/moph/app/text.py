"""Text normalization and tokens for Arabic + English search.

Arabic gets orthographic normalization and a light stemmer (Light10 style: strip common prefixes
and suffixes), so مستشفى / المستشفيات / مستشفيات all become مستشف. English gets the Snowball stemmer.
"""

import re

import snowballstemmer

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")  # incl. tatweel
_LETTERS = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
        **{chr(0x0660 + i): str(i) for i in range(10)},  # Arabic-Indic digits
        **{chr(0x06F0 + i): str(i) for i in range(10)},  # Persian digits
    }
)
_TOKEN = re.compile(r"[^\W_]+")
_ARABIC = re.compile(r"[؀-ۿ]")

_AR_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")
_AR_SUFFIXES = ("ها", "ان", "ات", "ون", "ين", "يه", "ه", "ي")

# Normalized forms. Includes Lebanese question words, since users write the way they speak.
_AR_STOP = {
    "في", "من", "علي", "الي", "عن", "مع", "هل", "ما", "ماذا", "كيف", "كيفيه", "متي", "اين", "هو",
    "هي", "انا", "انت", "هذا", "هذه", "ذلك", "التي", "الذي", "او", "ثم", "لا", "لم", "لن", "قد",
    "كان", "يكون", "اريد", "بدي", "شو", "قديش", "وين", "مين", "عند", "الي", "لي", "هيدا", "هيدي",
    "ليش", "عم", "رح", "كمان", "يا", "مش", "اذا", "ان", "انه", "كل", "بعد", "قبل", "به", "بها", "له",
    "لها", "منين", "شي", "جيب", "بجيب", "اجيب", "بدنا", "عطيني", "كيفي", "فيي", "فينا", "عندي", "ابي", "امي", "بس", "لازم", "يعني",
}

_english = snowballstemmer.stemmer("english")
_EN_STOP = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are", "be", "i", "my", "me",
    "we", "you", "your", "it", "this", "that", "what", "how", "do", "does", "can", "where", "who",
    "when", "which", "with", "from", "at", "by", "get", "need", "want", "have", "has", "about",
    "there", "if", "as", "am", "should", "would", "could", "please",
}


def normalize(text: str) -> str:
    """Lowercase, strip Arabic diacritics and tatweel, unify letter variants and digits."""
    return _DIACRITICS.sub("", text).translate(_LETTERS).lower()


def _stem_arabic(word: str) -> str:
    for prefix in _AR_PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 2:
            word = word[len(prefix):]
            break
    else:
        if word.startswith("و") and len(word) >= 4:
            word = word[1:]
    for suffix in _AR_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            word = word[: -len(suffix)]
    return word.rstrip("ء") or word


def tokens(text: str) -> list[str]:
    """Search tokens: normalized, stopwords dropped, stemmed."""
    out = []
    for word in _TOKEN.findall(normalize(text)):
        if _ARABIC.search(word):
            if word in _AR_STOP:
                continue
            stem = _stem_arabic(word)
        else:
            if word in _EN_STOP:
                continue
            stem = _english.stemWord(word) if not word.isdigit() else word
        if len(stem) >= 2:
            out.append(stem)
    return out


def is_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text))
