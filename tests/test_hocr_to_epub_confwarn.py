"""Unit tests for the low-confidence page notice in hocr-to-epub.

The per-page "only X% accurate" warning used to be prepended to every
affected page, announcing a number mid-reading that the reader cannot act
on. It now lives in the notice page: a short list of affected pages when
few are affected, otherwise a single sentence about the book as a whole.
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


def make_generator(tool, page_numbers=None, low=(), skipped=()):
    generator = tool.EpubGenerator.__new__(tool.EpubGenerator)
    generator.page_numbers = page_numbers or {}
    generator.low_confidence_pages = list(low)
    generator.skipped_low_confidence_pages = list(skipped)
    return generator


def test_no_warnings_no_notice(tool):
    generator = make_generator(tool)
    assert generator._confidence_notice(100) == ''


def test_short_list_with_printed_numbers(tool):
    generator = make_generator(
        tool, page_numbers={640: '626', 644: '630'},
        low=[(640, 42.0), (644, 40.0), (4, 44.0), (5, 43.0), (11, 45.0)])
    notice = generator._confidence_notice(600)
    assert 'printed pages 626, 630' in notice
    assert 'scan pages 4, 5, 11' in notice
    assert 'may contain many errors' in notice
    assert '44.00' not in notice      # the number is not announced


def test_single_printed_page(tool):
    generator = make_generator(tool, page_numbers={34: '12'},
                               low=[(34, 40.0)])
    notice = generator._confidence_notice(400)
    assert 'printed page 12' in notice
    assert 'printed pages' not in notice


def test_single_scan_page(tool):
    generator = make_generator(tool, low=[(1, 40.0)])
    notice = generator._confidence_notice(400)
    assert 'scan page 1' in notice


def test_many_pages_become_book_wide_sentence(tool):
    low = [(i, 40.0) for i in range(60)]
    generator = make_generator(tool, low=low)
    notice = generator._confidence_notice(100)
    assert '60 of 100 scanned pages' in notice
    assert '4' not in notice.replace('40.0', '')   # no page list


def test_all_pages_low(tool):
    low = [(i, 40.0) for i in range(50)]
    generator = make_generator(tool, low=low)
    notice = generator._confidence_notice(50)
    assert 'all 50 scanned pages' in notice


def test_skipped_pages_listed(tool):
    generator = make_generator(tool, skipped=[(7, 10.0), (9, 12.0)])
    notice = generator._confidence_notice(100)
    assert 'could not be read at all' in notice
    assert 'scan page 7' in notice and 'scan page 9' in notice


def test_accessibility_summary_mentions_notice(tool):
    generator = make_generator(tool, low=[(4, 40.0)])
    generator.has_text = True
    generator.has_images = False
    generator.toc_entries = []
    generator.book = tool.epub.EpubBook()
    generator.book.reset()
    generator.set_accessibility_metadata()
    summary = str(generator.book.metadata).lower()
    assert 'poor ocr quality' in summary
