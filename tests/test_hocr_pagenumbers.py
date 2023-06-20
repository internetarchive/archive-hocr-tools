import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')
@pytest.mark.usefixtures('sim_english_pagenumber_json_file')

def test_split_combine_plaintext(sim_hocr_file, sim_english_pagenumber_json_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    pagenumber_json_file = join(basedir, 'pagenumbers.json')

    check_call(['hocr-pagenumbers', '--density-threshold-pass-two', '0.1',
                '-f', sim_hocr_file, '-o', pagenumber_json_file])

    new = open(pagenumber_json_file, 'rb').read()
    old = open(sim_english_pagenumber_json_file, 'rb').read()

    assert old == new
