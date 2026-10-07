"""Heuristic classification of hOCR blocks into document structure.

This turns a text block plus a font-size measurement into a structural
role (heading of some level, or plain paragraph) and maps front-matter
headings to EPUB landmarks. It is deliberately small and self-contained:
the rules are English-only and tuned by eye, so the module can be inlined
into a single emitter if it stays fragile.

The functions take plain values (text, a font size, the body font size)
rather than hOCR elements, so callers can feed them from whatever data
shape they already have.
"""

import re
from collections import Counter

# Structural vocabulary. English only for now; non-English chapter words
# (chapitre, kapitel, ...) are not matched, which under-promotes their
# headings to size-based detection.
CHAPTER_RE = re.compile(
    r"^(chapter|part|book|canto|section|appendix|preface|introduction|"
    r"prologue|epilogue|contents|index|glossary|illustrations|"
    r"acknowledg|dedication|foreword|afterword|notes|bibliography)\b",
    re.I)

# Section titles that open with a leading article before the structural
# word, e.g. "THE BOOK OF DANIEL" (Kelly Link, The Book of Love) or "The
# Book of Ruth". Requiring all-caps or an enlarged font keeps ordinary
# sentences that happen to open with "The book ..." out of the headings.
CHAPTER_THE_RE = re.compile(
    r"^the\s+(chapter|part|book|canto|section|appendix|preface|introduction|"
    r"prologue|epilogue|contents|index|glossary|illustrations|"
    r"acknowledg|dedication|foreword|afterword|notes|bibliography)\b",
    re.I)

# A running head is set smaller than the body text; a real chapter title
# is not. All-caps lines at or below this fraction of the body size are
# treated as running heads, not headings. The same fraction decides which
# recurring top-of-page lines hocr-to-epub drops as furniture, so the two
# agree on the boundary.
RUNNING_HEAD_RATIO = 0.85

# A heading is short. A long line is a paragraph even if it matches a
# pattern or is set large (this stops a jacket blurb becoming a heading).
MAX_HEADING_LEN = 80

# Front-matter running heads / titles -> EPUB type landmarks.
FRONT_HEADS = (
    ("list of illustrations", "loi"),
    ("list of plates", "loi"),
    ("table of contents", "toc"),
    ("contents", "toc"),
    ("preface", "preface"),
    ("foreword", "foreword"),
    ("introduction", "introduction"),
    ("acknowledgment", "acknowledgments"),
    ("acknowledgement", "acknowledgments"),
    ("dedication", "dedication"),
    ("errata", "errata"),
)


def body_size(font_sizes):
    """Return the modal font size (the body text size), or 0.0 if unknown."""
    sizes = [s for s in font_sizes if s and s > 0]
    if not sizes:
        return 0.0
    return float(Counter(round(s) for s in sizes).most_common(1)[0][0])


def is_caps_heading(text):
    """A short all-caps line is usually a heading.

    Quoted all-caps lines are plate captions, not headings, so a leading
    quote disqualifies. Needs at least a few letters so stray rules or
    numerals do not read as headings.
    """
    letters = [c for c in text if c.isalpha()]
    return (4 <= len(letters) and len(text) <= 60
            and all(c.isupper() for c in letters)
            and not text.startswith(('"', "'", "\u201c", "\u2018")))


def classify(text, fontsize, body):
    """Classify a block as a heading or a paragraph.

    Returns ``('heading', level)`` where level is 1 or 2, or ``('para',)``.

    The text pattern is trusted first because a book may set its chapter
    headings at or below the body size; the font-size signal is only a
    secondary cue and is skipped when the body size is unknown.
    """
    text = (text or '').strip()
    if not text or len(text) > MAX_HEADING_LEN:
        return ('para',)

    if CHAPTER_RE.match(text):
        return ('heading', 1)

    # "THE BOOK OF DANIEL"-style titles: a leading article before the
    # structural word. Only trust it when the line is set in caps or is
    # enlarged, so ordinary sentences starting "The book ..." stay
    # paragraphs.
    if CHAPTER_THE_RE.match(text) and (
            is_caps_heading(text)
            or (body and fontsize >= body * 1.35)):
        return ('heading', 1)

    if body:
        if fontsize >= body * 1.8:
            return ('heading', 1)
        if fontsize >= body * 1.35:
            return ('heading', 2)
        if (is_caps_heading(text)
                and not (fontsize and fontsize <= body * RUNNING_HEAD_RATIO)):
            return ('heading', 2)

    return ('para',)


def front_matter_type(text):
    """Map a front-matter heading/title to an EPUB type, or None.

    Matches on the start of the (lower-cased) text so a running head like
    ``CONTENTS`` or a title like ``Table of Contents`` maps to ``toc``.
    """
    low = (text or '').strip().lower()
    for needle, kind in FRONT_HEADS:
        if low.startswith(needle):
            return kind
    return None


def is_chapter(text):
    """True if the text opens with a chapter marker.

    Narrower than ``CHAPTER_RE`` (which also matches front-matter titles
    like CONTENTS); used to find where the body matter starts.
    """
    return bool(re.match(r"(?i)chapter\b", (text or '').strip()))


def is_toc_entry(text):
    """True if a heading belongs in the table of contents.

    Matches the structural vocabulary or a front-matter type, so chapters,
    contents, index, illustrations and similar sections are included, while
    a large-font display line or OCR gibberish that merely got classified as
    a heading is not.
    """
    text = (text or '').strip()
    if CHAPTER_RE.match(text) or front_matter_type(text) is not None:
        return True
    return bool(CHAPTER_THE_RE.match(text) and is_caps_heading(text))


# Folio-like tokens that may be attached to a running head
# ("PREFACE. xi", "29 PRIDE AND PREJUDICE.", "THE BOOK OF LOVE 107").
DIGITS_TOKEN_RE = re.compile(r'^\d{1,4}$')
ROMAN_TOKEN_RE = re.compile(r'^[ivxlcdm]{1,5}$', re.I)
_ROMAN_VALUES = {'i': 1, 'v': 5, 'x': 10, 'l': 50,
                 'c': 100, 'd': 500, 'm': 1000}

# Common OCR confusions inside folio tokens ("3O" for "30", "I5" for "15").
_FOLIO_CONFUSIONS = str.maketrans({'O': '0', 'o': '0', 'l': '1', 'I': '1'})


def is_roman_numeral(token):
    """True if ``token`` is a grammatically valid roman numeral.

    Rejects ordinary words that happen to consist of roman symbols
    ("vivid", "civil", "mild") by checking numeral grammar.
    """
    low = token.lower()
    if not ROMAN_TOKEN_RE.match(low):
        return False
    values = [_ROMAN_VALUES[c] for c in low]
    for i, value in enumerate(values):
        if i + 1 < len(values) and value < values[i + 1]:
            # Subtractive pair: only I, X, C may subtract, and only from
            # the next-larger symbols (IV, IX, XL, XC, CD, CM).
            if value not in (1, 10, 100):
                return False
            if values[i + 1] not in (value * 5, value * 10):
                return False
    return True


def is_mostly_caps(text):
    """True if at least 80% of a line's letters are uppercase.

    Looser than ``is_caps_heading``: running heads like
    ``LIST OF ILLUSTRATIONS. xxvii`` carry a lowercase folio but still read
    as heads, while body text (dialogue, letters) does not.
    """
    alpha = [c for c in (text or '') if c.isalpha()]
    if len(alpha) < 3:
        return False
    return sum(1 for c in alpha if c.isupper()) >= 0.75 * len(alpha)


def carries_folio(text, folio):
    """True if the line's first or last token is the page's printed folio.

    Running heads often embed the page number ("THE BOOK OF LOVE 9",
    "29 PRIDE AND PREJUDICE."); a chapter heading whose number happens to
    match the folio ("Chapter 1" on page 1) is the exception, which is why
    callers require several folio-carrying occurrences before treating a
    recurring phrase as a running-head family.
    """
    folio = (folio or '').strip().lower()
    if not folio:
        return False
    tokens = (text or '').split()
    if not tokens:
        return False
    for token in (tokens[0], tokens[-1]):
        variants = {token.lower(),
                    token.translate(_FOLIO_CONFUSIONS).lower()}
        if any(variant == folio for variant in variants if variant):
            return True
    return False


def normalize_head_text(text):
    """Case-fold a line and collapse punctuation/whitespace.

    Used to compare lines across pages when detecting running heads, so
    "PRIDE AND PREJUDICE." and "Pride and prejudice" land on the same key.
    """
    text = re.sub(r'[^\w\s]', ' ', text or '')
    return ' '.join(text.lower().split())


def split_folio_token(text, folio):
    """Split a folio-like token off a line, returning ``(numeral, rest)``.

    A leading or trailing token is treated as the page's printed folio and
    removed when it is a roman numeral, or digits that appear inside the
    page's printed page number ("29 PRIDE AND PREJUDICE." ->
    ("29", "PRIDE AND PREJUDICE.")). Roman numerals are always removed
    since front-matter folios are roman while chapter headings keep their
    identity through the remaining text ("CHAPTER X" -> ("x", "CHAPTER")
    stays distinguishable from "CHAPTER XI" -> ("xi", "CHAPTER")).
    """
    tokens = text.split()
    if not tokens:
        return None, ''
    folio = (folio or '').strip().lower()
    for idx in (0, -1):
        token = tokens[idx]
        low = token.lower()
        # Folio digits, tolerating common OCR confusions ("3O" for "30",
        # "I5" for "15").
        variant = token.translate(_FOLIO_CONFUSIONS)
        if folio and DIGITS_TOKEN_RE.match(variant) and \
                variant.lower() in folio:
            rest = tokens[1:] if idx == 0 else tokens[:-1]
            return low, ' '.join(rest)
        if is_roman_numeral(token):
            rest = tokens[1:] if idx == 0 else tokens[:-1]
            return low, ' '.join(rest)
    return None, ' '.join(tokens)
