import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')


def test_search_inside(sim_hocr_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    lookup_table_file = join(basedir, 'table.json')
    sim_plaintext_file = join(basedir, 'plaintext.txt')
    sim_plaintext_hl_file = join(basedir, 'plaintext-hl.txt')

    lookup_table = check_output(['hocr-lookup-create', '-f', sim_hocr_file])
    with open(lookup_table_file, 'wb+') as f:
        f.write(lookup_table)

    plaintext = check_output(['hocr-text', '-f', sim_hocr_file])
    with open(sim_plaintext_file, 'wb+') as f:
        f.write(plaintext)

    plaintext_hl = check_output(['fts-text-annotate', '-f',
                                 sim_plaintext_file, '-p', 'English'])
    with open(sim_plaintext_hl_file, 'wb+') as f:
        f.write(plaintext_hl)

    search_matches = check_output(['fts-text-match', '--hocr',
                                   sim_hocr_file, '--annotated-text',
                                   sim_plaintext_hl_file, '--table',
                                   lookup_table_file])

    data = []
    for line in search_matches.decode('utf-8').split('\n'):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        data.append(d)

    known_data = json.load(open('test-files/hocr_search_sim_english_fts.json', 'r+'))

    assert data == known_data
