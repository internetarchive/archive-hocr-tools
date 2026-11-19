"""Where sections start, and where they must not.

The deriver cuts the book into one file per section at every level-1 heading,
and the reader's chapter list is those headings. Two mistakes make the books
the testers complained about: a chapter that is not recognised leaves its pages
in the previous file -- "one 655 KB file with two entries in the contents" --
and a heading that is really a running head or a recurring subhead invents a
chapter every time it appears.
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
    return tool.EpubGenerator.__new__(tool.EpubGenerator)


def h1(text, page, fontsize=100.0):
    return {'kind': 'heading', 'level': 1, 'page': page, 'top_y': 100,
            'text': text, 'fontsize': fontsize}


def para(text, page):
    return {'kind': 'para', 'page': page, 'top_y': 200, 'text': text}


def marker(page, html_text=None):
    return {'kind': 'marker', 'page': page, 'top_y': 0,
            'html': html_text or '<pb %d></pb>' % page}


def page(page_idx, *items):
    headings = [item['text'] for item in items
                if item['kind'] == 'heading' and item['level'] == 1]
    return {'page': page_idx, 'items': list(items), 'headings': headings,
            'has_words': True, 'has_images': False}


# --- reading a number as a chapter number -----------------------------------

@pytest.mark.parametrize('token,value', [
    ('i', 1), ('ix', 9), ('xiv', 14), ('xxviii', 28), ('mcm', 1900),
    ('iiii', None),      # not a written numeral
    ('mxmi', None),
    ('12', None),        # arabic is not roman
    ('', None),
])
def test_roman_value(token, value):
    assert structure.roman_value(token) == value


@pytest.mark.parametrize('text,expected', [
    ('1', True),
    ('7.', True),                       # "7." with the printed full stop
    ('XII', True),
    ('I', True),
    ('200', True),
    ('201', False),                     # not a chapter, something else
    ('1984', False),                    # a year set large
    ('Chapter 12', False),              # has words
    ('42 items', False),
    ('', False),
])
def test_is_bare_number(text, expected):
    assert structure.is_bare_number(text) is expected


# --- what a heading is allowed to start -------------------------------------

def test_a_bare_number_in_display_type_opens_a_chapter(generator):
    assert generator._section_kind('3', fontsize=110.0, body_size=52.0) \
        == 'chapter'


def test_the_same_numeral_at_text_size_opens_nothing(generator):
    """At text size this is a folio or a list entry, not a chapter."""
    assert generator._section_kind('3', fontsize=52.0, body_size=52.0) is None


def test_a_number_opens_nothing_when_the_body_size_is_unknown(generator):
    assert generator._section_kind('3', fontsize=110.0, body_size=0.0) is None


def test_a_year_in_display_type_opens_nothing(generator):
    assert generator._section_kind('1984', fontsize=110.0, body_size=52.0) \
        is None


def test_ordinary_headings_still_work(generator):
    assert generator._section_kind('CHAPTER VII', 40.0, 52.0) == 'chapter'
    assert generator._section_kind('PREFACE', 40.0, 52.0) == 'front'
    assert generator._section_kind('She walked to the', 40.0, 52.0) is None


def test_a_bare_number_belongs_in_the_contents():
    """Cutting the file at chapter six is half the job; the reader has to be
    able to jump there."""
    assert structure.is_toc_entry('6')
    assert structure.is_toc_entry('XII')
    assert not structure.is_toc_entry('1984')
    assert not structure.is_toc_entry('She walked to the')


# --- grouping ----------------------------------------------------------------

def test_chapters_open_at_bare_numbers(generator):
    pages = [page(1, h1('1', 1), para('it began', 1)),
             page(2, h1('2', 2, fontsize=110.0), para('and went on', 2))]

    sections = generator._group_sections(pages, body_size=52.0)

    assert [s['kind'] for s in sections] == ['chapter', 'chapter']
    assert [s['file'] for s in sections] == ['chapter_1.html',
                                             'chapter_2.html']


def test_a_recurring_heading_starts_no_section(generator):
    """A book with a "Chapter Summary" box on every chapter ends: the boxes are
    subheads, not chapters, and must not each become a contents entry."""
    pages = [page(p, h1('Chapter Summary', p),
                  para('what came before, page %d' % p, p))
             for p in range(1, 5)]

    sections = generator._group_sections(pages, body_size=52.0)

    assert len(sections) == 1
    assert sections[0]['headings'] == []
    assert sum(1 for item in sections[0]['items']
               if item['kind'] == 'heading') == 4


def test_a_heading_used_twice_is_still_a_section(generator):
    """A preface to the first edition and one to the second are two sections.
    Only a pattern of recurrence says "this is not a title"."""
    pages = [page(1, h1('PREFACE', 1), para('a', 1)),
             page(2, h1('PREFACE', 2), para('b', 2))]

    sections = generator._group_sections(pages, body_size=52.0)

    assert [s['kind'] for s in sections] == ['front', 'front']
    assert [s['title'] for s in sections] == ['PREFACE', 'PREFACE']


def test_a_contents_page_starts_no_chapters(generator):
    pages = [page(1, h1('CONTENTS', 1), h1('CHAPTER I', 1), h1('CHAPTER II', 1),
                  para('1  42', 1))]

    sections = generator._group_sections(pages, body_size=52.0)

    assert [s['kind'] for s in sections] == ['front']
    assert [s['title'] for s in sections] == ['CONTENTS']


def test_a_numbered_contents_list_starts_no_chapters(generator):
    """A modern contents page lists "1 / 2 / 3" as headings. The page is
    recognised by its shape, not by the word CONTENTS, which many books do not
    print legibly -- or at all."""
    generator.list_pages = {1}
    pages = [page(1, h1('1', 1), h1('2', 1), h1('3', 1),
                  para('1  7', 1))]

    sections = generator._group_sections(pages, body_size=52.0)

    assert len(sections) == 1
    assert sections[0]['kind'] == 'preamble'


# --- the size ceiling -------------------------------------------------------

def test_a_long_section_is_cut_between_paragraphs(generator):
    items = [para('x' * 200, 1) for _ in range(20)]

    parts = generator._split_items(items, limit=1200)

    assert len(parts) > 1
    assert [item for part in parts for item in part] == items
    assert all(len(generator._render_items(part)) <= 1200 for part in parts)


def test_a_split_never_closes_on_a_pagebreak_or_a_heading(generator):
    """A marker left at the end of a file would point "page 12" at the bottom
    of the previous page, and a heading on its own looks like an empty
    chapter."""
    items = []
    for page_idx in range(1, 12):
        items.append(para('x' * 200, page_idx))
        items.append(marker(page_idx + 1))
        items.append(h1('HEADING %d' % page_idx, page_idx))

    parts = generator._split_items(items, limit=1200)

    assert len(parts) > 1
    for part in parts[:-1]:
        assert part[-1]['kind'] == 'para'


def test_a_block_bigger_than_the_ceiling_gets_its_own_file(generator):
    """It cannot be cut, but the walk has to get past it rather than stop."""
    huge = para('y' * 5000, 1)
    items = [huge, para('after it', 2)]

    parts = generator._split_items(items, limit=1000)

    assert parts[0] == [huge]
    assert len(parts) == 2


def test_the_parts_are_named_titled_and_listed(generator):
    items = [para('x' * 200, 1) for _ in range(20)]
    sections = [{'kind': 'chapter', 'title': 'INDEX', 'file': 'chapter_1.html',
                 'headings': ['INDEX'], 'items': items}]

    out = generator._cap_section_sizes(sections, limit=1200)

    assert len(out) > 1
    assert out[0]['file'] == 'chapter_1.html'
    assert out[0]['title'] == 'INDEX'
    assert out[1]['file'] == 'chapter_1_part_2.html'
    assert out[1]['title'] == 'INDEX (continued)'
    # A continuation has no heading of its own; the entry is stated.
    assert out[1]['headings'] == []
    assert out[1]['toc_title'] == 'INDEX (continued)'
    assert [item for part in out for item in part['items']] == items


def test_a_section_inside_the_ceiling_is_left_alone(generator):
    sections = [{'kind': 'chapter', 'title': 'CHAPTER I',
                 'file': 'chapter_1.html', 'headings': ['CHAPTER I'],
                 'items': [para('short', 1)]}]

    assert generator._cap_section_sizes(sections, limit=1200) == sections


# --- when nothing was recognised as a chapter opening -----------------------

def unwritten_book(pages=70):
    """A book with no heading the deriver understands: one long preamble."""
    return [page(i, para('text of printed page %d' % i, i), marker(i))
            for i in range(pages)]


def test_a_book_without_chapter_openings_is_cut_at_the_printed_pages(generator):
    pages = unwritten_book()

    sections = generator._group_sections(pages, body_size=52.0)

    assert set(section['kind'] for section in sections) == {'chapter'}
    assert [section['title'] for section in sections] == [
        'Pages 1\u201320', 'Pages 21\u201340', 'Pages 41\u201360',
        'Pages 61\u201370']
    assert all(section['toc_title'] for section in sections), \
        'each part needs an entry the reader can jump to'
    assert sum(len(s['items']) for s in sections) == \
        sum(len(p['items']) for p in pages)


def test_the_page_labels_use_the_numbers_the_book_prints(generator):
    generator.page_numbers = {0: '112', 19: '131', 20: '132', 39: '151'}

    sections = generator._group_sections(unwritten_book(), body_size=52.0)

    assert sections[0]['title'] == 'Pages 112\u2013131'
    assert sections[1]['title'] == 'Pages 132\u2013151'


def test_a_label_never_mixes_two_page_numberings(generator):
    """Front matter is unnumbered in most books. Saying "Pages 2–6" for
    twenty leaves because one end happens to carry a printed number would tell
    the reader to scroll somewhere they are not."""
    generator.page_numbers = {20: '6'}

    sections = generator._group_sections(unwritten_book(), body_size=52.0)

    assert sections[0]['title'] == 'Pages 1\u201320'


def test_a_book_with_chapters_is_not_cut_up(generator):
    pages = [page(0, h1('CHAPTER I', 0), para('a', 0))] + unwritten_book(70)[1:]

    sections = generator._group_sections(pages, body_size=52.0)

    assert len(sections) == 1
    assert sections[0]['kind'] == 'chapter'
    assert sections[0]['title'] == 'CHAPTER I'


def test_a_short_book_is_left_as_one_file(generator):
    pages = unwritten_book(30)

    sections = generator._group_sections(pages, body_size=52.0)

    assert [section['kind'] for section in sections] == ['preamble']


def test_files_stay_unique_across_kinds(generator):
    pages = [page(1, para('unheading start', 1)),
             page(2, h1('PREFACE', 2), para('p', 2)),
             page(3, h1('CHAPTER I', 3), para('c', 3)),
             page(4, h1('PREFACE', 4), para('p2', 4))]

    sections = generator._group_sections(pages, body_size=52.0)
    files = [s['file'] for s in sections]

    assert len(files) == len(set(files))
    assert files == ['preamble.html', 'front_1.html', 'chapter_1.html',
                     'front_2.html']
