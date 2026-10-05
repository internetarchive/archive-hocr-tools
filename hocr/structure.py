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

# A running head is set smaller than the body text; a real chapter title
# is not. All-caps lines at or below this fraction of the body size are
# treated as running heads, not headings.
RUNNING_HEAD_RATIO = 0.8

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
    return bool(CHAPTER_RE.match(text)) or front_matter_type(text) is not None
