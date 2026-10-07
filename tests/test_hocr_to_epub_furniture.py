"""Unit tests for the running-head furniture pass in hocr-to-epub.

The pass is what keeps running heads ("PRIDE AND PREJUDICE.",
"THE BOOK OF LOVE 107", "PREFACE. xi") out of the prose, the headings and
the ToC. These tests drive the decision logic directly with synthetic
occurrences so the rules stay observable without a full conversion run.
"""
import importlib.machinery
import importlib.util
from os.path import dirname, join

import pytest


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


def make_generator(tool, page_numbers=None):
    generator = tool.EpubGenerator.__new__(tool.EpubGenerator)
    generator.page_numbers = page_numbers or {}
    return generator


def occurrence(page, raw, fontsize, page_numbers=None, body=50.0):
    """Build an occurrence the same way the collection pass does."""
    import hocr.structure
    _numeral, rest = hocr.structure.split_folio_token(
        raw, (page_numbers or {}).get(page, ''))
    return {'page': page, 'raw': raw, 'fontsize': fontsize,
            'norm': hocr.structure.normalize_head_text(rest)}


def test_running_head_family_is_dropped(tool):
    """A phrase repeating at the top of many pages is furniture."""
    page_numbers = {i: str(i - 30) for i in range(40, 60)}
    occs = [occurrence(i, 'PRIDE AND PREJUDICE.', 14, page_numbers)
            for i in range(40, 60)]
    occs += [occurrence(i, 'Some body text line here.', 50, page_numbers)
             for i in range(40, 44)]
    generator = make_generator(tool, page_numbers)
    drop = generator._decide_furniture(occs, 50.0)
    # Every running head occurrence is dropped, the body text is not.
    assert all((o['page'], o['norm']) in drop for o in occs[:20])
    assert not any((o['page'], o['norm']) in drop for o in occs[20:])


def test_folio_styled_family_keeps_nothing(tool):
    """Heads that embed the page's own folio are never kept as headings,
    even when they would classify as one."""
    page_numbers = {i: str(i - 30) for i in range(40, 50)}
    occs = [occurrence(i, 'THE BOOK OF LOVE %d' % (i - 30), 37,
                       page_numbers)
            for i in range(40, 50)]
    generator = make_generator(tool, page_numbers)
    drop = generator._decide_furniture(occs, 50.0)
    assert len(drop) == 10


def test_chapter_headings_recurrence_keeps_each_run(tool):
    """Chapter headings that recur as running heads keep the first
    occurrence of every run, so each chapter survives."""
    # "CHAPTER X" style: the heading on the opening page, then the same
    # text as a running head on the following pages.
    occs = []
    for start in (40, 80, 120):
        occs.append(occurrence(start, 'CHAPTER X', 33))
        for page in range(start + 1, start + 4):
            occs.append(occurrence(page, 'CHAPTER X', 33))
    generator = make_generator(tool)
    drop = generator._decide_furniture(occs, 50.0)
    kept_pages = {o['page'] for o in occs} - {p for p, _n in drop}
    assert kept_pages == {40, 80, 120}


def test_isolated_recurring_body_text_is_safe(tool):
    """Two identical dialogue lines far apart are not furniture."""
    occs = [occurrence(100, 'she said.', 50), occurrence(400, 'she said.', 52)]
    generator = make_generator(tool)
    drop = generator._decide_furniture(occs, 50.0)
    assert drop == set()


def test_body_sized_occurrences_are_kept(tool):
    """Occurrences set at body size or larger are never dropped."""
    page_numbers = {i: str(i) for i in (10, 200)}
    occs = [occurrence(10, 'THE BOOK OF DANIEL', 55, page_numbers),
            occurrence(200, 'THE BOOK OF DANIEL', 56, page_numbers)]
    generator = make_generator(tool, page_numbers)
    drop = generator._decide_furniture(occs, 50.0)
    assert drop == set()


def test_preface_running_head_keeps_first_heading(tool):
    """A front-matter head recurring on consecutive pages keeps exactly
    one heading (the first one that classifies as a heading)."""
    occs = [occurrence(14, 'X PREFACE.', 13)]
    occs += [occurrence(i, 'PREFACE. %s' % roman, 14)
             for i, roman in enumerate(
                 ['xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi'], start=15)]
    generator = make_generator(tool)
    drop = generator._decide_furniture(occs, 50.0)
    dropped_pages = {p for p, _n in drop}
    assert 14 in dropped_pages            # "X PREFACE." is not a heading
    assert 15 not in dropped_pages        # first heading survives
    assert dropped_pages == {14, 16, 17, 18, 19, 20}


def test_mangled_variant_joins_family(tool):
    """An OCR-mangled head ("THE BOOK OF LOVE of") is dropped like the
    head it extends."""
    page_numbers = {i: str(i - 30) for i in range(40, 46)}
    occs = [occurrence(i, 'THE BOOK OF LOVE %d' % (i - 30), 37,
                       page_numbers) for i in range(40, 45)]
    occs.append(occurrence(45, 'THE BOOK OF LOVE of', 37, page_numbers))
    generator = make_generator(tool, page_numbers)
    drop = generator._decide_furniture(occs, 50.0)
    assert (45, 'the book of love of') in drop
