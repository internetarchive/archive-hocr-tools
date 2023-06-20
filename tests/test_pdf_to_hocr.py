import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('pdf_file')
@pytest.mark.usefixtures('pdf_metadata_file')
@pytest.mark.usefixtures('pdf_chocr_file')

def test_pdf_to_hocr(pdf_file, pdf_metadata_file, pdf_chocr_file):
    pdf_file = str(pdf_file)
    pdf_metadata_file = str(pdf_metadata_file)
    pdf_chocr_file = str(pdf_chocr_file)

    basedir = dirname(pdf_file)

    pdf_chocr_out = join(basedir, 'pdf-chocr.html')

    pdf_chocr = check_output(['pdf-to-hocr', '-J', pdf_metadata_file, '-f', pdf_file])
    orig_text = open(pdf_chocr_file, 'rb+').read()

    assert pdf_chocr == orig_text
