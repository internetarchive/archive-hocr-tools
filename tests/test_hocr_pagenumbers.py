import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')
@pytest.mark.usefixtures('sim_english_pagenumber_json_file')

def test_hocr_pagenumbers(sim_hocr_file, sim_english_pagenumber_json_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    pagenumber_json_file = join(basedir, 'pagenumbers.json')

    check_call(['hocr-pagenumbers', '-f', sim_hocr_file, '-o', pagenumber_json_file])

    new = json.load(open(pagenumber_json_file, 'rb'))
    old = json.load(open(sim_english_pagenumber_json_file, 'rb'))

    assert old == new
