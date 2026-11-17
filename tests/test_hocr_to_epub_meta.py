"""Accessibility metadata in hocr-to-epub (round 4 items 2, 3 and 4).

The catalogue summary and its ``schema:`` properties are the only thing a
reader sees before choosing the file, so they must describe *this* build:
one recommended hazard value, no ``accessibilityControl`` claims (those
belong to the reading app), and an explicit statement when the print
edition's illustrations were left out.
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


def build_metadata(tool, has_text=True, has_images=False,
                   print_illustrations=False, toc_entries=(),
                   page_numbers=None, low_confidence=()):
    generator = tool.EpubGenerator.__new__(tool.EpubGenerator)
    generator.has_text = has_text
    generator.has_images = has_images
    generator.print_illustrations = print_illustrations
    generator.toc_entries = list(toc_entries)
    generator.page_numbers = page_numbers or {}
    generator.low_confidence_pages = list(low_confidence)
    generator.skipped_low_confidence_pages = []
    generator.book = tool.epub.EpubBook()
    generator.book.reset()
    generator.set_accessibility_metadata()
    return generator.book


def schema(book, prop):
    """Values of one ``schema:`` property as the book carries them."""
    values = []
    for elements in book.metadata.values():
        for element, entries in elements.items():
            if element != 'meta':
                continue
            for text, attr in entries:
                if (attr or {}).get('property') == prop:
                    values.append(text)
    return values


def summary(book):
    return ' '.join(schema(book, 'schema:accessibilitySummary'))


# ------------------------------------------------------------------ hazard

def test_one_hazard_value_and_it_is_none(tool):
    """The single recommended value replaces the three no...Hazard ones;
    it displays the same and is what the vocabulary asks for."""
    book = build_metadata(tool)
    assert schema(book, 'schema:accessibilityHazard') == ['none']


@pytest.mark.parametrize('stale', [
    'noFlashingHazard', 'noMotionSimulationHazard', 'noSoundHazard',
])
def test_old_hazard_values_are_gone(tool, stale):
    assert stale not in str(build_metadata(tool).metadata)


# ---------------------------------------------------------------- control

def test_no_accessibility_control_claim(tool):
    """The W3C vocabulary does not apply accessibilityControl to a resource
    that is not integrated with its user interface: keyboard, touch and
    voice control are the reading app's business, not the file's."""
    book = build_metadata(tool)
    assert schema(book, 'schema:accessibilityControl') == []


# ------------------------------------------------------- illustrations gap

def test_dropped_illustrations_are_announced(tool):
    """A build that left the scan's pictures out says so, instead of being
    silent now that the alternative-text sentence no longer applies."""
    book = build_metadata(tool, print_illustrations=True)
    assert ('Illustrations from the print edition are not included.'
            in summary(book))


def test_book_without_illustrations_stays_silent(tool):
    """A text-only scan that never had plates must not claim any were
    dropped, so the sentence keys on the recorded picture boxes."""
    book = build_metadata(tool, print_illustrations=False)
    assert 'not included' not in summary(book)


def test_build_with_images_reports_missing_alt_text_instead(tool):
    book = build_metadata(tool, has_images=True, print_illustrations=True)
    text = summary(book)
    assert 'missing meaningful alternative text' in text
    assert 'are not included' not in text


@pytest.mark.parametrize(
    ('has_text', 'has_images', 'modes'),
    [
        (True, False, ['textual']),
        (True, True, ['textual', 'visual']),
        (False, True, ['visual']),
    ],
)
def test_access_modes_follow_the_content(tool, has_text, has_images, modes):
    book = build_metadata(tool, has_text=has_text, has_images=has_images)
    assert schema(book, 'schema:accessMode') == modes
    assert schema(book, 'schema:accessModeSufficient') == modes


# ------------------------------------------------- features (unchanged)

def test_features_are_still_derived_from_the_content(tool):
    """Guards the earlier feature-derivation work against these edits."""
    book = build_metadata(
        tool, toc_entries=[('chapter_1.html', 'CHAPTER I')],
        page_numbers={20: '6'})
    features = schema(book, 'schema:accessibilityFeature')
    assert 'displayTransformability' in features
    assert 'tableOfContents' in features
    assert 'structuralNavigation' in features
    assert 'pageBreakMarkers' in features
    assert 'pageNavigation' in features


def test_nothing_claimed_when_nothing_was_emitted(tool):
    book = build_metadata(tool, has_text=False)
    assert schema(book, 'schema:accessibilityFeature') == ['none']


def test_low_confidence_pages_point_at_the_notice(tool):
    book = build_metadata(tool, low_confidence=[(4, 40.0)])
    assert 'poor ocr quality' in summary(book).lower()
