"""Leftover page numbers (folios) in hocr-to-epub.

A printed page has a number and usually a running title; OCR carries both into
the text. The furniture pass drops them, but a lone numeral is only safe to
call "the page's number" when the scan data says so: the same characters are a
roman numeral, a chapter number, a contents entry, or the tail of a misread
word. These tests cover the decision, not just the happy path.
"""
import importlib.machinery
import importlib.util
from os.path import dirname, join

import pytest

import hocr.structure as structure


def load_tool():
    here = dirname(__file__)
    loader = importlib.machinery.SourceFileLoader(
        'hocr_to_epub', join(here, '..', 'bin', 'hocr-to-epub'))
    spec = importlib.util.spec_from_loader('hocr_to_epub', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def tool():
    return load_tool()


@pytest.fixture
def generator(tool):
    """A generator with just what the furniture pass reads."""
    gen = tool.EpubGenerator.__new__(tool.EpubGenerator)
    gen.page_numbers = {0: '9', 1: '10', 2: '11', 3: '12', 4: '13'}
    return gen


def head(page, text='PRIDE AND PREJUDICE.', fontsize=6):
    return {'page': page, 'raw': text, 'fontsize': fontsize,
            'norm': structure.normalize_head_text(text), 'numeral': None}


def folio(page, numeral, fontsize=6):
    return {'page': page, 'raw': numeral, 'fontsize': fontsize, 'norm': '',
            'numeral': numeral.lower()}


# --- which numeral counts as this page's number -----------------------------

@pytest.mark.parametrize('numeral,folio,expected', [
    ('10', '10', True),        # the ordinary case
    ('3o', '30', True),        # OCR read a zero as the letter o
    ('53', '353', True),       # leading digit lost
    ('xii', 'xii', True),
    ('v', 'vii', False),       # a stray letter is not a truncated roman
    ('m', '', False),          # nothing to match against: claim nothing
    ('', '12', False),
    ('xii', '12', False),      # roman and arabic do not cross over
    ('9', '119', True),        # digits inside the printed number
])
def test_folio_matches_token(numeral, folio, expected):
    assert structure.folio_matches_token(numeral, folio) is expected


# --- contents and index pages ------------------------------------------------

def test_contents_page_is_list_shaped():
    lines = ['Covering a screen 38', 'Heading to Chapter X 61',
             'No, no ; stay where you are 84', 'Pride 97', '105',
             'Mrs. Bennet 120', 'Index of entries 133']
    assert structure.is_list_shaped(lines)


def test_prose_page_is_not_list_shaped():
    lines = ['It is a truth universally acknowledged, that a single man in',
             'possession of a good fortune, must be in want of a wife.',
             'However little known the feelings or views of such a man may',
             'be on his first entering a neighbourhood, this truth is',
             'so well fixed in the minds of the surrounding families,',
             'that he is considered as the rightful property of some one',
             'or other of their daughters.']
    assert not structure.is_list_shaped(lines)


def test_recipe_page_is_not_list_shaped():
    """A cookbook is full of numbers, but they open the line, not close it."""
    lines = ['2 cups flour', '1 teaspoon salt', '3 eggs', '1 cup milk',
             'Mix the dry ingredients, add the eggs and beat smooth.']
    assert not structure.is_list_shaped(lines)


def test_a_short_page_is_never_list_shaped():
    assert not structure.is_list_shaped(['22', '24', '26'])


# --- the drop decision -------------------------------------------------------

def test_folio_drops_survive_when_a_running_head_was_found(generator):
    """The folio list used to be reset by the family pass, so every page kept
    its printed number as its own paragraph."""
    occurrences = [head(p) for p in range(5)]
    occurrences += [folio(p, generator.page_numbers[p]) for p in range(5)]

    drop = generator._decide_furniture(occurrences, body_size=10)

    assert all((p, '') in drop for p in range(5))
    assert all((p, 'pride and prejudice') in drop for p in range(5))


def test_folio_only_pages_are_dropped_when_nothing_else_recurs(generator):
    occurrences = [folio(p, generator.page_numbers[p]) for p in range(4)]

    drop = generator._decide_furniture(occurrences, body_size=10)

    assert drop == {(p, '') for p in range(4)}


def test_a_numeral_that_is_not_the_pages_number_is_kept(generator):
    """A lone "m" is a misread letter, not folio 9."""
    occurrences = [folio(0, 'm'), folio(1, '48'), folio(2, 'mmm')]

    assert generator._decide_furniture(occurrences, body_size=10) == set()


def test_a_numeral_printed_larger_than_the_text_is_kept(generator):
    """Chapter openers put a bare number above the text at display size."""
    occurrences = [folio(0, '9', fontsize=46), folio(1, '10', fontsize=51)]

    assert generator._decide_furniture(occurrences, body_size=10) == set()


def test_numbers_on_a_contents_page_are_content(generator):
    occurrences = [folio(0, '9'), folio(1, '10')]

    drop = generator._decide_furniture(occurrences, body_size=10,
                                       list_pages={0, 1})

    assert drop == set()


def test_without_scan_data_no_number_is_claimed(generator):
    generator.page_numbers = {}

    assert generator._decide_furniture([folio(0, '12')], body_size=10) == set()


# --- what may be looked at in the foot band ---------------------------------

@pytest.mark.parametrize('raw,numeral,folio,expected', [
    ('53', '53', '53', True),                  # the page's own number
    ('24 THE BOOK OF LOVE', None, '24', True),  # a running foot, number in it
    ('24 THE BOOK OF LOVE', None, '88', False),  # not this page's number
    ('*If using self-rising flour, omit the salt', None, '112', False),
    ('Chapter Summary', None, '112', False),
    ('9', '9', '', True),                      # numeral alone still qualifies
])
def test_only_a_number_makes_a_foot_band_line_a_candidate(
        tool, raw, numeral, folio, expected):
    assert tool.EpubGenerator._foot_band_candidate(raw, numeral, folio) \
        is expected


# --- applying the decision to a line ----------------------------------------

def line(text, top=10, size=6):
    return {'bbox': (0, top, 100, top + 8),
            'words': [{'text': text, 'fontsize': size}]}


def test_an_ornament_line_is_not_taken_with_the_folio(generator):
    """Both normalize to the empty string, so a "***" on a page whose folio is
    dropped used to go with it."""
    occurrences = [folio(0, '9'), {'page': 0, 'raw': '***', 'fontsize': 6,
                                   'norm': '', 'numeral': None}]
    generator.furniture_drop = generator._decide_furniture(occurrences,
                                                           body_size=10)

    assert generator._is_furniture_line(0, line('9'), page_height=1000)
    assert not generator._is_furniture_line(0, line('***'), page_height=1000)


def test_a_line_between_the_bands_is_never_furniture(generator):
    """The middle of the page is the text block, whatever the key says."""
    occurrences = [folio(0, '9')]
    generator.furniture_drop = generator._decide_furniture(occurrences,
                                                           body_size=10)

    assert not generator._is_furniture_line(0, line('9', top=500),
                                            page_height=1000)


def test_a_folio_at_the_foot_of_the_page_is_furniture_too(generator):
    """Plates that print their number below the text were untouched."""
    occurrences = [folio(0, '9')]
    generator.furniture_drop = generator._decide_furniture(occurrences,
                                                           body_size=10)

    assert generator._is_furniture_line(0, line('9', top=950),
                                        page_height=1000)


@pytest.mark.parametrize('top,expected', [
    (0, True), (120, True),      # head band of a 1000-high page
    (121, False), (500, False),  # the text block
    (879, False), (880, True), (999, True),   # foot band
])
def test_band_boundaries(generator, top, expected):
    assert generator._in_furniture_band(top, 1000) is expected


def test_the_band_does_not_need_a_page_height(generator):
    """A page without usable dimensions cannot be banded, so everything is a
    candidate and the recurrence rules decide on their own."""
    assert generator._in_furniture_band(500, 0)
