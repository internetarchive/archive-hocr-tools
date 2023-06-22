import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('abbyy_file')
@pytest.mark.usefixtures('abbyy_to_hocr_file')

def test_pdf_to_hocr(abbyy_file, abbyy_to_hocr_file):
    abbyy_file = str(abbyy_file)
    abbyy_to_hocr_file = str(abbyy_to_hocr_file)

    basedir = dirname(abbyy_file)

    chocr_out = join(basedir, 'chocr.html')

    chocr_data = check_output(['abbyy-to-hocr', '-f', abbyy_file])

    orig_chocr = check_output(['xmllint', '--format', abbyy_to_hocr_file])
    chocr_data = check_output(['xmllint', '--format', '-'], input=chocr_data)

    assert orig_chocr == chocr_data
