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
    ("illustrations", "loi"),
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
    if is_bare_number(text):
        # A chapter opened with just its number is still a chapter: this is
        # where a reader looks for "6" when the book says chapter six.
        return True
    return bool(CHAPTER_THE_RE.match(text) and is_caps_heading(text))


# Words that stay lowercase inside a title-case label unless they open it.
LABEL_SMALL_WORDS = frozenset((
    'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'into',
    'nor', 'of', 'on', 'or', 'the', 'to', 'with', 'yet'))


def label_case(text):
    """Title-case an all-caps heading for a reader-facing label.

    File ``<title>``, table-of-contents entries and landmark labels are read
    out loud and shown in reading-system interfaces, where the OCR's
    "CHAPTER VII" is neither. Only a line that is *mostly* uppercase is retitled:
    a heading the OCR already set in mixed case keeps its own capitalisation,
    so proper nouns the book itself capitalised survive.

    Roman numerals keep their caps ("Chapter VII", not "Chapter Vii"), tokens
    without letters are left alone ("Room 12"), and a hyphenated compound
    capitalises both halves ("Non-Verbal").
    """
    text = text or ''
    stripped = text.strip()
    if not stripped or not is_mostly_caps(stripped):
        return text

    words = []
    for index, token in enumerate(stripped.split()):
        core = ''.join(c for c in token if c.isalpha())
        if not core:
            words.append(token)                 # digits or punctuation
        elif len(core) >= 2 and is_roman_numeral(core, max_len=15):
            words.append(token)                 # VII, XXVIII, ...
        elif index > 0 and core.lower() in LABEL_SMALL_WORDS:
            words.append(token.lower())
        else:
            words.append(_capitalize_token(token))
    return ' '.join(words)


def _capitalize_token(token):
    """Lower-case ``token``, then capitalise the first letter of each part.

    The first *letter* is capitalised rather than the first character, so
    attached punctuation is untouched ("(see" -> "(see", "(SEE" -> "(See").
    A part after a hyphen or slash is capitalised too ("NON-VERBAL" ->
    "Non-Verbal").
    """
    chars = []
    capitalize = True
    for char in token.lower():
        if capitalize and char.isalpha():
            chars.append(char.upper())
            capitalize = False
        else:
            chars.append(char)
        if char in '-/\u2010\u2011\u2012\u2013\u2014':
            capitalize = True
    return ''.join(chars)


# Folio-like tokens that may be attached to a running head
# ("PREFACE. xi", "29 PRIDE AND PREJUDICE.", "THE BOOK OF LOVE 107").
DIGITS_TOKEN_RE = re.compile(r'^\d{1,4}$')
# Length is checked separately (see ``is_roman_numeral``), so one pattern
# covers both a short folio and a long chapter numeral.
ROMAN_TOKEN_RE = re.compile(r'^[ivxlcdm]{1,15}$', re.I)
_ROMAN_VALUES = {'i': 1, 'v': 5, 'x': 10, 'l': 50,
                 'c': 100, 'd': 500, 'm': 1000}

# Common OCR confusions inside folio tokens ("3O" for "30", "I5" for "15").
_FOLIO_CONFUSIONS = str.maketrans({'O': '0', 'o': '0', 'l': '1', 'I': '1'})


def is_roman_numeral(token, max_len=5):
    """True if ``token`` is a grammatically valid roman numeral.

    Rejects ordinary words that happen to consist of roman symbols
    ("vivid", "civil", "mild") by checking numeral grammar.

    ``max_len`` is 5 because a printed folio is short; callers that mean
    chapter numerals ("XXVIII") pass a larger bound.
    """
    low = token.lower()
    if len(low) > max_len or not ROMAN_TOKEN_RE.match(low):
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


# A chapter number this large is not a chapter: it is a year, a page count or
# an amount that happened to be set large.
MAX_CHAPTER_NUMBER = 200

_ROMAN_VALUES = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500,
                 'm': 1000}


def _to_roman(number):
    out = []
    for value, numeral in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
                           (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
                           (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'),
                           (1, 'i')):
        while number >= value:
            out.append(numeral)
            number -= value
    return ''.join(out)


def roman_value(token):
    """Value of a roman numeral, or None if it is not one.

    It has to be a *written* numeral, not merely a string of roman letters:
    the loose character class that recognises a folio also accepts "iiii" and
    "mxmi", and a misread folio must not become chapter four. Round-tripping
    through the canonical spelling is what tells them apart.
    """
    token = (token or '').strip().lower()
    if not token or not ROMAN_TOKEN_RE.match(token):
        return None
    total = 0
    previous = 0
    for char in reversed(token):
        value = _ROMAN_VALUES.get(char)
        if value is None:
            return None
        total += value if value >= previous else -value
        previous = max(previous, value)
    return total if _to_roman(total) == token else None


def is_bare_number(text):
    """True for a heading that is a chapter number and nothing else.

    Plenty of books open a chapter with just "1" or "XII", and a line that is
    only a numeral is otherwise the very shape of a leftover folio. Callers
    have to bring the evidence that separates the two -- a chapter number is
    set as display type where a folio is set small, and a folio sits in the
    head or foot band that the furniture pass has already cleared -- and this
    only says the shape is possible.
    """
    token = (text or '').strip().strip('.) \t\u2013\u2014')
    if not token or len(token.split()) != 1:
        return False
    if token.isdigit():
        return 0 < int(token) <= MAX_CHAPTER_NUMBER
    value = roman_value(token)
    return value is not None and 0 < value <= MAX_CHAPTER_NUMBER


def is_folio_only(text):
    """True if the text is nothing but a printed page number.

    A leftover folio ("53", "xvii", "37.") reads as a sentence with no
    terminator, so a joining pass welds it onto the neighbouring sentence.
    Only a single token counts: "Chapter 12" is not a folio.
    """
    token = (text or '').strip().strip('.,;:()\u2013\u2014-')
    if not token or len(token.split()) != 1:
        return False
    return bool(DIGITS_TOKEN_RE.match(token)) or is_roman_numeral(token)


def folio_matches_token(numeral, folio):
    """True if a stripped numeral is a readable form of this page's folio.

    Calling a line "the page's number" is only safe when one can say whose
    number it is: a lone "m" is a roman numeral, a misread folio and the tail
    of a decorated initial by turns, and only the scan data's printed folio
    settles it. Truncation is tolerated for digits ("53" for "353") because
    losing a leading digit is a common OCR failure; a roman numeral has to
    match exactly, since its letters are ordinary letters elsewhere.
    """
    numeral = (numeral or '').strip().lower()
    folio = (folio or '').strip().lower()
    if not numeral or not folio:
        return False
    variant = numeral.translate(_FOLIO_CONFUSIONS)
    if variant == folio:
        return True
    return variant.isdigit() and variant in folio


def is_list_shaped(lines, min_lines=6, min_fraction=0.4):
    """True for contents and index pages: short lines ending in a number.

    On such a page the numbers are the content, so "this lone number is a
    folio" must not be applied to it. The shape is distinctive enough to
    detect without reading a single word: many lines, few tokens each, and the
    last token of most of them a number.
    """
    lines = [line for line in (lines or []) if line and line.strip()]
    if len(lines) < min_lines:
        return False
    ending = sum(1 for line in lines
                 if len(line.split()) <= 6
                 and is_folio_only(line.split()[-1]))
    return ending >= max(4, min_fraction * len(lines))


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
