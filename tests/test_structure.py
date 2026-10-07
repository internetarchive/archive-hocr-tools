import pytest

from hocr.structure import (body_size, carries_folio, classify,
                            front_matter_type, is_caps_heading,
                            is_mostly_caps, is_roman_numeral,
                            is_toc_entry, normalize_head_text,
                            split_folio_token)


@pytest.mark.parametrize(
    ('sizes', 'expected'),
    [
        ([50, 50, 50, 40], 50.0),
        ([40, 40, 50], 40.0),
        ([0, 0], 0.0),
        ([], 0.0),
    ],
)
def test_body_size(sizes, expected):
    assert body_size(sizes) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('ALL CAPS HEADING', True),
        ('"A QUOTED LINE"', False),      # quoted all-caps is a caption
        ('Mixed Case', False),
        ('AB', False),                   # too few letters
        ('', False),
    ],
)
def test_is_caps_heading(text, expected):
    assert is_caps_heading(text) is expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('LIST OF ILLUSTRATIONS. xxvii', True),   # lowercase folio is fine
        ('THE BOOK OF LOVE 9', True),
        ('she said.', False),
        ('The book was on the table.', False),
        ('ab', False),                            # too few letters
        ('', False),
    ],
)
def test_is_mostly_caps(text, expected):
    assert is_mostly_caps(text) is expected


@pytest.mark.parametrize(
    ('text', 'fontsize', 'body', 'expected'),
    [
        # Pattern wins even when set smaller than the body.
        ('CHAPTER I', 37, 50, ('heading', 1)),
        ('PART TWO', 50, 50, ('heading', 1)),
        ('INTRODUCTION', 50, 50, ('heading', 1)),
        # "THE BOOK OF ..." titles (leading article before the structural
        # word) are headings when set in caps or enlarged...
        ('THE BOOK OF DANIEL', 55, 58, ('heading', 1)),
        ('The Book of Love: A Novel', 90, 50, ('heading', 1)),
        # ...but ordinary sentences opening with "The book" are not.
        ('The book was on the table.', 50, 50, ('para',)),
        # Size-driven headings.
        ('A BIG DISPLAY TITLE', 95, 50, ('heading', 1)),   # >= 1.8x body
        ('Medium Title', 70, 50, ('heading', 2)),          # >= 1.35x body
        # All-caps at body size is a heading.
        ('ALL CAPS HEADING', 50, 50, ('heading', 2)),
        # All-caps but running-head-sized is not a heading.
        ('RUNNING HEAD', 35, 50, ('para',)),
        ('PRIDE AND PREJUDICE.', 14, 17, ('para',)),
        # Long text is never a heading, even if large.
        ('A' * 100, 95, 50, ('para',)),
        # Empty is a paragraph.
        ('', 50, 50, ('para',)),
        # With no known body size, only the pattern makes a heading.
        ('CHAPTER II', 40, 0, ('heading', 1)),
        ('THE BOOK OF DANIEL', 55, 0, ('heading', 1)),
        ('Medium Title', 70, 0, ('para',)),
    ],
)
def test_classify(text, fontsize, body, expected):
    assert classify(text, fontsize, body) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('CONTENTS', 'toc'),
        ('Table of Contents', 'toc'),
        ('PREFACE', 'preface'),
        ('List of Illustrations', 'loi'),
        ('Dedication', 'dedication'),
        ('CHAPTER I', None),
        ('', None),
    ],
)
def test_front_matter_type(text, expected):
    assert front_matter_type(text) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('CHAPTER I', True),
        ('ILLUSTRATIONS', True),
        ('PREFACE', True),
        # "THE BOOK OF ..." titles belong in the ToC when set in caps...
        ('THE BOOK OF DANIEL', True),
        # ...but a sentence starting with "The book" does not.
        ('The book was on the table.', False),
        ('A big display line', False),
        ('', False),
    ],
)
def test_is_toc_entry(text, expected):
    assert is_toc_entry(text) is expected


@pytest.mark.parametrize(
    ('token', 'expected'),
    [
        ('i', True),
        ('xi', True),
        ('xxvii', True),
        ('XL', True),
        ('cm', True),
        # Ordinary words made of roman symbols are rejected by grammar.
        ('vivid', False),
        ('civil', False),
        ('mild', False),
        ('lid', False),
        ('', False),
        ('hello', False),
    ],
)
def test_is_roman_numeral(token, expected):
    assert is_roman_numeral(token) is expected


def test_normalize_head_text():
    assert normalize_head_text('PRIDE  AND   PREJUDICE.') == \
        'pride and prejudice'
    assert normalize_head_text('The Book of Love') == 'the book of love'
    assert normalize_head_text('') == ''


@pytest.mark.parametrize(
    ('text', 'folio', 'numeral', 'rest'),
    [
        # Trailing folio digits are removed, including OCR confusions.
        ('THE BOOK OF LOVE 107', '107', '107', 'THE BOOK OF LOVE'),
        ('29 PRIDE AND PREJUDICE.', '29', '29', 'PRIDE AND PREJUDICE.'),
        ('PRIDE AND PREJUDICE. I 5', '15', '5',
         'PRIDE AND PREJUDICE. I'),
        ('3O PRIDE AND PREJUDICE.', '30', '3o',
         'PRIDE AND PREJUDICE.'),
        # Roman folios are removed even when the printed number is unknown.
        ('PREFACE. xi', '', 'xi', 'PREFACE.'),
        ('X PREFACE.', '', 'x', 'PREFACE.'),
        # A chapter number that is not the folio is kept...
        ('CHAPTER 12', '57', None, 'CHAPTER 12'),
        # ...unless it appears inside the printed folio.
        ('CHAPTER 5', '15', '5', 'CHAPTER'),
        # Nothing to strip.
        ('PRIDE AND PREJUDICE.', '30', None, 'PRIDE AND PREJUDICE.'),
        ('', '', None, ''),
    ],
)
def test_split_folio_token(text, folio, numeral, rest):
    assert split_folio_token(text, folio) == (numeral, rest)


@pytest.mark.parametrize(
    ('text', 'folio', 'expected'),
    [
        ('THE BOOK OF LOVE 9', '9', True),
        ('29 PRIDE AND PREJUDICE.', '29', True),
        ('3O PRIDE AND PREJUDICE.', '30', True),   # OCR confusion
        ('CHAPTER 1', '1', True),                  # heading on page 1
        ('PRIDE AND PREJUDICE.', '29', False),
        ('PREFACE. xi', '', False),
        ('', '9', False),
    ],
)
def test_carries_folio(text, folio, expected):
    assert carries_folio(text, folio) is expected
