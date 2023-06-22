import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')
@pytest.mark.usefixtures('sim_hocr_file_text')

def test_hocr_text(sim_hocr_file, sim_hocr_file_text):
    sim_hocr_file = str(sim_hocr_file)
    sim_hocr_file_text = str(sim_hocr_file_text)
    basedir = dirname(sim_hocr_file)

    plain_file = join(basedir, 'folded.html')

    plain_text = check_output(['hocr-text', '-f', sim_hocr_file])

    with open(sim_hocr_file_text, 'rb') as fp:
        prev_plaintext = fp.read()

    assert prev_plaintext == plain_text

