"""Illustrations in hocr-to-epub.

A plate is cropped out of the scan and put into the page it came from. Two
things then go wrong if it is treated as just another block in the reading
order: it is announced as a picture with no name, and it interrupts a sentence
that continues on the next page, so the reader gets half a clause, a picture,
and then the rest of the clause.
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


@pytest.fixture
def generator(tool):
    return tool.EpubGenerator.__new__(tool.EpubGenerator)


def para(text, page):
    return {'kind': 'para', 'page': page, 'top_y': 0, 'text': text}


def marker(page):
    return {'kind': 'marker', 'page': page, 'top_y': 0,
            'html': '<pb %d></pb>' % page}


def image(src, page):
    return {'kind': 'image', 'page': page, 'top_y': 0, 'src': src}


def heading(text, page):
    return {'kind': 'heading', 'page': page, 'top_y': 0, 'level': 1,
            'text': text}


# --- how a plate is marked up -----------------------------------------------

def test_a_plate_is_a_figure_and_not_announced(generator):
    """With no caption and no description, "image" is all a screen reader
    would say, so it says nothing instead."""
    html = generator._render_items([image('image_0012_00.jpeg', 12)])

    assert html == ('<figure><img src="image_0012_00.jpeg" alt="" '
                    'role="presentation"/></figure>')


def test_text_still_renders_around_a_plate(generator):
    html = generator._render_items([para('Her father had been an', 12),
                                    image('i.jpeg', 12),
                                    para('attorney in Meryton', 12)])

    assert '<p>Her father had been an</p>' in html
    assert '<figure>' in html and '<p>attorney in Meryton</p>' in html


# --- where a plate sits when the sentence continues -------------------------

def test_a_plate_does_not_split_a_sentence(generator):
    """One sentence across a page turn, with the plate in the way: the
    paragraph stays whole and the plate goes after it."""
    items = [para('Her father had been an', 12),
             image('plate.jpeg', 12),
             marker(13),
             para('attorney in Meryton.', 13)]

    out = generator._join_paragraphs(items)

    assert len(out) == 2
    para_item, plate = out
    assert para_item['kind'] == 'para'
    assert para_item['text'] == ('Her father had been an <pb 13></pb>'
                                 'attorney in Meryton.')
    assert plate['kind'] == 'image'


def test_a_plate_stays_put_when_the_paragraphs_do_not_join(generator):
    items = [para('Her father had been an attorney.', 12),
             image('plate.jpeg', 12),
             marker(13),
             para('Mr. Bennet was quite disconcerted.', 13)]

    out = generator._join_paragraphs(items)

    assert [item['kind'] for item in out] == ['para', 'image', 'marker',
                                              'para']
    assert out[2]['page'] == 13


def test_a_plate_between_a_marker_and_the_text_stays_after_the_marker(generator):
    items = [para('an', 12),
             marker(13),
             image('plate.jpeg', 13),
             para('attorney in Meryton.', 13)]

    out = generator._join_paragraphs(items)

    # The paragraph joins, the plate follows it, and the marker is inside the
    # paragraph at the join point -- it must not end up behind the plate.
    assert out[0]['text'].index('<pb 13>') < out[0]['text'].index(
        'attorney in Meryton.')
    assert [item['kind'] for item in out] == ['para', 'image']


def test_a_heading_still_interrupts_the_sentence_even_with_a_plate(generator):
    items = [para('Her father had been an', 12),
             image('plate.jpeg', 12),
             heading('CHAPTER XIII', 13),
             para('attorney in Meryton.', 13)]

    out = generator._join_paragraphs(items)

    assert [item['kind'] for item in out] == ['para', 'image', 'heading',
                                              'para']


def test_several_plates_all_follow_the_paragraph(generator):
    items = [para('the two halves of one', 12),
             image('a.jpeg', 12),
             marker(13),
             image('b.jpeg', 13),
             para('sentence.', 13)]

    out = generator._join_paragraphs(items)

    assert out[0]['text'] == 'the two halves of one <pb 13></pb>sentence.'
    assert [item['kind'] for item in out[1:]] == ['image', 'image']
    assert [item['src'] for item in out[1:]] == ['a.jpeg', 'b.jpeg']
