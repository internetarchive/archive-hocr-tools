import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')

def test_split_combine_plaintext(sim_hocr_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    split_pages = join(basedir, 'split-%06d.html')
    split_pages_g = join(basedir, 'split-*.html')
    combined_file = join(basedir, 'combined.html')

    check_call(['hocr-split-pages', '-f', sim_hocr_file, '-o', split_pages])
    combined_text = check_output(['hocr-combine-stream', '-g', split_pages_g])

    with open(combined_file, 'wb+') as f:
        f.write(combined_text)

    plaintext = check_output(['hocr-text', '-f', sim_hocr_file])
    new_plaintext = check_output(['hocr-text', '-f', combined_file])

    assert plaintext == new_plaintext

