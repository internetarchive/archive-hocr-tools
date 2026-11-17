"""Paragraph joining and pagebreak placement in hocr-to-epub.

The joining pass merges the two halves of a sentence that a page turn (or
an OCR paragraph break) split apart, and moves the pagebreak marker to the
join point inside the merged paragraph. When the halves are *not* joined,
the marker still has to sit at the first word of its own page: a marker
flushed in front of the previous page's paragraph makes "go to page N" land
on page N-1, which is round 5 item 1.

These drive the pass with synthetic item lists, so every branch is
observable without a full conversion run.
"""
import importlib.machinery
import importlib.util
import re
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


@pytest.fixture(scope='module')
def joiner(tool):
    """A generator with just what the joining pass reads."""
    generator = tool.EpubGenerator.__new__(tool.EpubGenerator)
    return generator


def para(text, page):
    return {'kind': 'para', 'page': page, 'top_y': 0, 'text': text}


def marker(page):
    return {'kind': 'marker', 'page': page, 'top_y': 0,
            'html': '<pb %d></pb>' % page}


def hr(page):
    return {'kind': 'hr', 'page': page, 'top_y': 0}


def heading(text, page, level=1):
    return {'kind': 'heading', 'page': page, 'top_y': 0, 'level': level,
            'text': text}


def kinds(items):
    return [(item['kind'], item.get('text', item.get('html')))
            for item in items]


def marker_pages(items):
    """Pages of the markers in an item list, inline ones included.

    A marker that was merged into a paragraph lives inside its text, so both
    forms have to be counted to see whether any page break went missing.
    """
    pages = []
    for item in items:
        if item['kind'] == 'marker':
            pages.append(item['page'])
        elif item['kind'] == 'para':
            pages.extend(int(num) for num in
                         re.findall(r'<pb (\d+)></pb>', item['text']))
    return pages


# ---------------------------------------------------------------- joining

def test_sentence_split_across_a_page_is_joined(joiner):
    out = joiner._join_paragraphs([
        para('Her father had been an', 10),
        marker(11),
        para('attorney in Meryton', 11),
    ])
    assert [item['kind'] for item in out] == ['para']
    assert out[0]['text'] == \
        'Her father had been an <pb 11></pb>attorney in Meryton'


def test_refused_join_keeps_the_marker_after_the_earlier_paragraph(joiner):
    """The round 5 regression.

    A proper noun after the page turn means the halves stay separate (the
    lowercase rule is deliberately conservative). The marker used to be
    flushed in front of the first half, so the reader who asked for page 11
    was taken to page 10's text.
    """
    out = joiner._join_paragraphs([
        para('She walked to the', 10),
        marker(11),
        para('London bridge', 11),
    ])
    assert kinds(out) == [
        ('para', 'She walked to the'),
        ('marker', '<pb 11></pb>'),
        ('para', 'London bridge'),
    ]


def test_refused_join_after_a_terminator_keeps_the_marker_with_page_11(joiner):
    out = joiner._join_paragraphs([
        para('She walked home.', 10),
        marker(11),
        para('It was already late', 11),
    ])
    assert [item['kind'] for item in out] == ['para', 'marker', 'para']
    assert out[1]['page'] == 11


def test_marker_between_paragraphs_is_not_moved_before_a_heading(joiner):
    out = joiner._join_paragraphs([
        para('The end of the chapter', 10),
        marker(11),
        heading('CHAPTER II', 11),
        para('It began again', 11),
    ])
    assert [item['kind'] for item in out] == ['para', 'marker',
                                             'heading', 'para']
    assert out[1]['page'] == 11


def test_marker_after_a_join_is_not_lost_or_moved(joiner):
    """The paragraph consumed page 11's first line and then stopped; the
    page 12 marker collected behind it still has to be emitted, after the
    merged paragraph rather than dropped."""
    out = joiner._join_paragraphs([
        para('one half of a', 10),
        marker(11),
        para('sentence, and here is more', 11),
        marker(12),
        para('A new sentence starts', 12),
    ])
    assert [item['kind'] for item in out] == ['para', 'marker', 'para']
    assert out[0]['text'] == ('one half of a <pb 11></pb>'
                              'sentence, and here is more')
    assert out[1]['page'] == 12
    assert out[2]['text'] == 'A new sentence starts'


def test_consecutive_markers_all_land_at_the_join_point(joiner):
    """Two page turns can pile up on one short paragraph (plates carry no
    text of their own); both markers belong at the join, in page order."""
    out = joiner._join_paragraphs([
        para('a sentence that runs', 10),
        marker(11),
        marker(12),
        para('across two page turns', 12),
    ])
    assert [item['kind'] for item in out] == ['para']
    assert out[0]['text'] == ('a sentence that runs <pb 11></pb>'
                              '<pb 12></pb>across two page turns')


def test_heading_between_halves_stops_the_join(joiner):
    out = joiner._join_paragraphs([
        para('and the sentence would', 10),
        marker(11),
        heading('CHAPTER II', 11),
        para('have gone on', 11),
    ])
    assert [item['kind'] for item in out] == ['para', 'marker',
                                             'heading', 'para']
    assert out[0]['text'] == 'and the sentence would'


# ------------------------------------------------------- marker invariant

# Every branch above, plus a couple of shapes the fixtures show: a stray
# folio paragraph between the halves, and a run of markers with no
# paragraph after them at all.
INVARIANT_CASES = [
    ('joined', [para('half of a', 10), marker(11), para('sentence', 11)]),
    ('refused lowercase',
     [para('She walked to the', 10), marker(11), para('London', 11)]),
    ('refused terminator',
     [para('She walked home.', 10), marker(11), para('It was late', 11)]),
    ('stray folio between the halves',
     [para('Her father had been an', 10), para('53', 10), marker(11),
      para('attorney in Meryton', 11)]),
    ('join then refusal',
     [para('one half of a', 10), marker(11), para('sentence, more', 11),
      marker(12), para('New sentence', 12)]),
    ('markers at the end of a section',
     [para('the last line', 10), marker(11), marker(12)]),
    ('heading interrupts',
     [para('and the sentence would', 10), marker(11),
      heading('CHAPTER II', 11), para('have gone on', 11)]),
    ('no markers at all', [para('one', 1), para('two', 1)]),
]


@pytest.mark.parametrize('name,items', INVARIANT_CASES,
                         ids=[case[0] for case in INVARIANT_CASES])
def test_no_pagebreak_lands_on_an_earlier_pages_text(joiner, name, items):
    """A marker for page N may never be followed by text from before N.

    This is the whole of round 5 item 1 in one assertion: items reach the
    joining pass in page order, so a marker that ends up in front of an
    earlier page's paragraph points "go to page N" at page N-1.
    """
    out = joiner._join_paragraphs(items)

    seen = None
    for item in out:
        if item['kind'] == 'marker':
            seen = item['page']
        elif seen is not None and item.get('page', 0) < seen:
            pytest.fail('page %s text follows the marker for page %s (%s)'
                        % (item['page'], seen, name))


@pytest.mark.parametrize('name,items', INVARIANT_CASES,
                         ids=[case[0] for case in INVARIANT_CASES])
def test_joining_never_loses_a_pagebreak(joiner, name, items):
    """Every marker in must still be in the output, in the same order: the
    page-list and the NCX are built from these."""
    out = joiner._join_paragraphs(items)
    assert marker_pages(out) == marker_pages(items)


def test_joining_keeps_every_word(joiner):
    items = [para('one half of a', 10), marker(11), para('sentence here', 11),
             marker(12), para('Next page text', 12)]
    out = joiner._join_paragraphs(items)
    text = ' '.join(item['text'] for item in out if item['kind'] == 'para')
    for fragment in ('one half of a', 'sentence here', 'Next page text'):
        assert fragment in text


# ------------------------------------------------------------ hyphenation

def test_hyphenated_word_joins_when_continuation_is_lowercase(joiner):
    """The word is rebuilt, and the page break stays inside it: the word
    really is split across the two pages."""
    out = joiner._join_paragraphs([
        para('the art\x7f', 10),
        marker(11),
        para('ists painted it', 11),
    ])
    assert [item['kind'] for item in out] == ['para']
    assert out[0]['text'] == 'the art<pb 11></pb>ists painted it'
    assert re.sub(r'<pb \d+></pb>', '', out[0]['text']) == \
        'the artists painted it'


def test_hyphen_placeholder_stripped_when_nothing_continues(joiner):
    """'before-' + 'THE END': the word is complete, so the placeholder goes
    away and the two paragraphs stay apart."""
    out = joiner._join_paragraphs([
        para('until before\x7f', 10),
        marker(11),
        para('THE END', 11),
    ])
    assert [item['kind'] for item in out] == ['para', 'marker', 'para']
    assert out[0]['text'] == 'until before'
    assert '\x7f' not in str(kinds(out))


# --------------------------------------------------------- continues_sentence

@pytest.mark.parametrize(
    ('first', 'second', 'expected'),
    [
        ('Her father had been an', 'attorney in Meryton', True),
        ('Her father had been an', 'The attorney in Meryton', False),
        ('Her father had been an.', 'attorney in Meryton', False),
        ('the art\x7f', 'ists', True),
        ('before\x7f', 'THE END', False),
        ('', 'attorney', False),
        ('a tail', '', False),
        # A leftover folio is not the end of a sentence, and merging it in
        # puts "53" inside the next sentence.
        ('53', 'attorney in Meryton', False),
        ('Her father had been an', '37', False),
        ('xvii', 'attorney in Meryton', False),
    ],
)
def test_continues_sentence(joiner, first, second, expected):
    assert joiner._continues_sentence(first, second) is expected


# ------------------------------------------------------------------- fuzzing

def _random_items(rng):
    """A random item stream shaped like a real page run: paragraphs in page
    order, markers at the page boundaries, the occasional heading or rule."""
    items = []
    page = 1
    for _ in range(rng.randrange(1, 14)):
        roll = rng.random()
        if roll < 0.18:
            items.append(marker(page))
            page += rng.choice([1, 1, 1, 2])
        elif roll < 0.26:
            items.append(heading('CHAPTER %d' % page, page))
        elif roll < 0.30:
            items.append(hr(page))
        else:
            tail = rng.choice(['a sentence that ends', 'a clause that ran',
                               'the art\x7f', 'a complete stop.', '53',
                               'xvii', '42 items', ''])
            head = rng.choice(['and it went on', 'London bridge', 'ists',
                               'A new one', '37', ''])
            items.append(para(tail, page))
            if rng.random() < 0.5:
                items.append(marker(page + 1))
                page += 1
                items.append(para(head, page))
    return items


def test_fuzz_invariants(joiner):
    """The two invariants over random streams (fixed seed: deterministic).

    Guards the loop arithmetic in _join_paragraphs: the index must always
    advance (no hang), markers must survive, and none may end up in front of
    an earlier page's text.
    """
    import random
    rng = random.Random(20261116)
    for _ in range(2000):
        items = _random_items(rng)
        out = joiner._join_paragraphs(items)          # hangs if i stalls
        assert marker_pages(out) == marker_pages(items)
        seen = None
        for entry in out:
            if entry['kind'] == 'marker':
                seen = entry['page']
            elif seen is not None and entry.get('page', 0) < seen:
                pytest.fail('marker for page %s precedes page %s text in %r'
                            % (seen, entry.get('page'), items))
        # a placeholder at the end of a paragraph always resolves: either the
        # next paragraph continues the word, or the word is complete and the
        # placeholder is dropped
        assert '\x7f' not in ''.join(
            entry.get('text', '') for entry in out)
