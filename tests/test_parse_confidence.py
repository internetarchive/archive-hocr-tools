import io

import pytest

from hocr.parse import (hocr_page_iterator, hocr_page_to_word_data,
                        hocr_page_to_word_data_fast)

HOCR = b"""<html><body>
<div class='ocr_page' title='bbox 0 0 100 100; ppageno 0'>
<div class='ocr_carea' title='bbox 0 0 100 100'>
<p class='ocr_par'>
<span class='ocr_line' title='bbox 0 0 100 20'>
<span class='ocrx_word' title='bbox 0 0 50 20; x_wconf %s'>hello</span>
</span>
</p>
</div>
</div>
</body></html>"""


def _first_word(func, conf):
    page = next(hocr_page_iterator(io.BytesIO(HOCR % conf)))
    return func(page)[0]['lines'][0]['words'][0]


@pytest.mark.parametrize('func', [hocr_page_to_word_data,
                                  hocr_page_to_word_data_fast])
@pytest.mark.parametrize('conf,expected', [(b'96', 96), (b'96.5', 96.5)])
def test_word_confidence(func, conf, expected):
    word = _first_word(func, conf)
    assert word['confidence'] == expected
