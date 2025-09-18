from __future__ import annotations

import re
from typing import Optional


def _try_third_party(text: str) -> Optional[str]:
    """Try third-party deasciifiers if installed. Return None if none available.

    Packages tried (in order):
    - turkish_deasciifier (PyPI: turkish-deasciifier)
    - trnlp.deasciifier (if present)
    """
    # 1) turkish-deasciifier
    try:
        from turkish_deasciifier import Deasciifier  # type: ignore

        return Deasciifier(text).convert_to_turkish()
    except Exception:
        pass

    # 2) TRNLP (if provides deasciifier)
    try:
        from trnlp import Deasciifier as TRDeasciifier  # type: ignore

        return TRDeasciifier(text).convert_to_turkish()
    except Exception:
        pass

    return None


# Conservative fallback mapping rules.
# These are intentionally minimal to avoid over-conversion.
_BASIC_REPLACEMENTS = [
    # Specific whole words first
    (r"\bcagri\b", "çağrı"),
    (r"\bCagri\b", "Çağrı"),
    (r"\bsarki\b", "şarkı"),
    (r"\bSarki\b", "Şarkı"),
    # Common patterns that are very likely Turkish
    (r"\bsi", "şi"),
    (r"\bS[İi]", "Şi"),
    (r"\bSu", "Şu"),
    (r"\bis", "iş"),
    (r"\bIc", "İç"),
    (r"\bic", "iç"),
    (r"\bCok", "Çok"),
    (r"\bcok", "çok"),
    (r"\bCunku", "Çünkü"),
    (r"\bcunku", "çünkü"),
    (r"\bGuzel", "Güzel"),
    (r"\bguzel", "güzel"),
    (r"\bOgr", "Öğr"),
    (r"\bogr", "öğr"),
    (r"\bSark", "Şark"),
    (r"\bsark", "şark"),
    (r"\bCag", "Çağ"),
    (r"\bcag", "çağ"),
]


_LETTER_MAP = {
    # These are only applied in a context-sensitive way (see below)
    "c": "ç",
    "g": "ğ",
    "i": "ı",  # ambiguous; handled conservatively
    "o": "ö",
    "s": "ş",
    "u": "ü",
    "C": "Ç",
    "G": "Ğ",
    "I": "İ",
    "O": "Ö",
    "S": "Ş",
    "U": "Ü",
}


_VOWELS = set("aeıioöuüAEIİOÖUÜ")


def _soft_heuristic(word: str) -> str:
    """Apply gentle letter replacements inside a word using heuristics.

    Heuristics are intentionally conservative to avoid damaging English words.
    """
    chars = list(word)
    n = len(chars)
    for i, ch in enumerate(chars):
        rep = None

        if ch == "s":
            # ş is common before i,e,a,u,ı,o,ö,ü at word start or after consonant
            prev = chars[i - 1] if i > 0 else ""
            nxt = chars[i + 1] if i + 1 < n else ""
            if (i == 0 or prev not in _VOWELS) and nxt.lower() in "ieaıouöü":
                rep = "ş"
        elif ch == "c":
            nxt = chars[i + 1] if i + 1 < n else ""
            # More conservative: ç mostly before a/o/u in many common words
            if nxt.lower() in "aou":
                rep = "ç"
        # avoid broad g/ğ and o/ö u/ü heuristics in fallback
        elif ch == "I":
            # In Turkish, uppercase I with dot is İ
            rep = "İ"
        elif ch == "i":
            # Common pattern: ğ + ı
            prev = chars[i - 1] if i > 0 else ""
            if prev == "ğ":
                rep = "ı"

        if rep:
            chars[i] = rep

    return "".join(chars)


def deasciify(text: str) -> str:
    """Convert ASCII-typed Turkish to proper Turkish letters.

    Tries third-party deasciifier if available; otherwise uses a conservative
    heuristic fallback aimed to help common cases without overcorrection.
    """
    third = _try_third_party(text)
    if third is not None:
        return third

    # Apply some safe replacements for very common patterns
    res = text
    for pat, repl in _BASIC_REPLACEMENTS:
        res = re.sub(pat, repl, res)

    # Process word by word with heuristics
    def _proc_word(w: str) -> str:
        # Skip very short or all-caps words
        if len(w) < 3 or (w.isupper() and not any(ch in "iI" for ch in w)):
            return w
        return _soft_heuristic(w)

    tokens = re.split(r"(\s+)", res)
    for i in range(0, len(tokens), 2):
        if i < len(tokens):
            tokens[i] = _proc_word(tokens[i])
    return "".join(tokens)
