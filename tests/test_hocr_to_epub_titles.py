"""Reader-facing labels in hocr-to-epub.

File titles, table-of-contents entries and landmark labels are shown and
spoken by reading systems, so they are title-cased and named for what the
document is. The book's own name belongs in the OPF and the NCX docTitle, not
in the navigation document.
"""
import importlib.machinery
import importlib.util
import tempfile
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


def test_nav_is_titled_as_the_contents_list(tool):
    """ebooklib fills the nav <title> and the toc <h2> with the book title."""
    import ebooklib.epub as epub
    book = epub.EpubBook()
    book.reset()
    book.language = 'en'
    book.set_title('Pride and prejudice')
    book.toc = [epub.Link('chapter_1.html', 'Chapter I', 'toc_0')]
    book.guide = [{'type': 'toc', 'title': 'Contents', 'href': 'f.html'}]
    nav = epub.EpubNav()
    book.add_item(nav)
    writer = tool.LangEpubWriter(
        join(tempfile.gettempdir(), 'nav_title_test.epub'), book, {})

    tree_str = writer._get_nav(nav)
    assert b'<title>Table of Contents</title>' in tree_str
    assert b'<h2>Table of Contents</h2>' in tree_str
    assert b'Pride and prejudice' not in tree_str
    # The other navs keep their own headings.
    assert b'<h2>Guide</h2>' in tree_str
