import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')

def test_fold_chars(sim_hocr_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    folded_file = join(basedir, 'folded.html')

    folded_text = check_output(['hocr-fold-chars', '-f', sim_hocr_file])

    with open(folded_file, 'wb+') as f:
        f.write(folded_text)

    plaintext = check_output(['hocr-text', '-f', sim_hocr_file])
    new_plaintext = check_output(['hocr-text', '-f', folded_file])

    assert plaintext == new_plaintext

