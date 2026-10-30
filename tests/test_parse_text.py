import io

import pytest

from hocr.parse import (hocr_page_iterator, hocr_page_to_word_data,
                        hocr_page_to_word_data_fast)

HOCR = b"""<html><body>
<div class='ocr_page' title='bbox 0 0 100 100; ppageno 0'>
<div class='ocr_carea' title='bbox 0 0 100 100'>
<p class='ocr_par'>
<span class='ocr_line' title='bbox 0 0 100 20'>
<span class='ocrx_word' title='bbox 0 0 50 20; x_wconf 90'>%s</span>
</span>
</p>
</div>
</div>
</body></html>"""


def _first_word(func, inner):
    page = next(hocr_page_iterator(io.BytesIO(HOCR % inner)))
    return func(page)[0]['lines'][0]['words'][0]


@pytest.mark.parametrize('func', [hocr_page_to_word_data,
                                  hocr_page_to_word_data_fast])
@pytest.mark.parametrize('inner,expected', [
    (b'plain', 'plain'),
    (b'<b>bold</b>', 'bold'),
    (b'<b><i>nested</i></b>', 'nested'),
    (b'some&amp;word.<sup>8</sup>', 'some&word.8'),
    (b'<i>a</i>bc', 'abc'),
    (b'x<i>y</i>z', 'xyz'),
    (b'<b>a</b><i>b</i>', 'ab'),
])
def test_word_text(func, inner, expected):
    assert _first_word(func, inner)['text'] == expected


@pytest.mark.parametrize('func', [hocr_page_to_word_data,
                                  hocr_page_to_word_data_fast])
def test_empty_word_raises(func):
    with pytest.raises(ValueError):
        _first_word(func, b'<b></b>')
