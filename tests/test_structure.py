import pytest

from hocr.structure import (body_size, classify, front_matter_type,
                           is_caps_heading)


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
    ('text', 'fontsize', 'body', 'expected'),
    [
        # Pattern wins even when set smaller than the body.
        ('CHAPTER I', 37, 50, ('heading', 1)),
        ('PART TWO', 50, 50, ('heading', 1)),
        ('INTRODUCTION', 50, 50, ('heading', 1)),
        # Size-driven headings.
        ('A BIG DISPLAY TITLE', 95, 50, ('heading', 1)),   # >= 1.8x body
        ('Medium Title', 70, 50, ('heading', 2)),          # >= 1.35x body
        # All-caps at body size is a heading.
        ('ALL CAPS HEADING', 50, 50, ('heading', 2)),
        # All-caps but running-head-sized is not a heading.
        ('RUNNING HEAD', 35, 50, ('para',)),
        # Long text is never a heading, even if large.
        ('A' * 100, 95, 50, ('para',)),
        # Empty is a paragraph.
        ('', 50, 50, ('para',)),
        # With no known body size, only the pattern makes a heading.
        ('CHAPTER II', 40, 0, ('heading', 1)),
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
