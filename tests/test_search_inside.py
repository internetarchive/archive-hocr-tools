import pytest
from subprocess import check_output, check_call
from os.path import dirname, join

import json

@pytest.mark.usefixtures('sim_hocr_file')
@pytest.mark.usefixtures('sim_hocr_lookup_file')
@pytest.mark.usefixtures('sim_hocr_searchtext_file')


def test_search_inside(sim_hocr_file, sim_hocr_lookup_file, sim_hocr_searchtext_file):
    sim_hocr_file = str(sim_hocr_file)
    basedir = dirname(sim_hocr_file)

    lookup_table_file = join(basedir, 'table.json')
    sim_plaintext_file = join(basedir, 'plaintext.txt')
    sim_plaintext_hl_file = join(basedir, 'plaintext-hl.txt')

    lookup_table = check_output(['hocr-lookup-create', '-f', sim_hocr_file])
    with open(lookup_table_file, 'wb+') as f:
        f.write(lookup_table)

    assert open(str(sim_hocr_lookup_file), 'rb').read() == lookup_table

    plaintext = check_output(['hocr-text', '-f', sim_hocr_file])
    with open(sim_plaintext_file, 'wb+') as f:
        f.write(plaintext)

    assert open(str(sim_hocr_searchtext_file), 'rb').read() == plaintext

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


class TestMatchWords:
    def test_match_words_empty(self):
        from hocr.fts import match_words

        hocr_words = []
        match_indices = []
        assert match_words(hocr_words, match_indices) == []

        hocr_words = [{'text': 'test'}]
        match_indices = []
        assert match_words(hocr_words, match_indices) == []

        hocr_words = []
        match_indices = [(0, 1)]
        assert match_words(hocr_words, match_indices) == []

    def test_match_words(self):
        from hocr.fts import match_words

        # Failing case from https://webarchive.jira.com/browse/WEBDEV-4873
        text = """organized in Chicago, Illinois on September 29-30, 1900, made a trip to England. After arrival there he found that there was an Association known as <IA_FTS_MATCH>The Commercial Travelers</IA_FTS_MATCH>’ Christian Association already in existence."""
        hocr_words = [
            {'text': word}
            for word in text.replace('<IA_FTS_MATCH>', '').replace('</IA_FTS_MATCH>', '').split()
        ]
        match_indices = [(149, 173)]

        assert match_words(hocr_words, match_indices) == [
            [
                {'text': 'The'},
                {'text': 'Commercial'},
                {'text': 'Travelers’'},
            ]
        ]

    def test_match_words_multiple(self):
        from hocr.fts import match_words

        text = """organized in Chicago, Illinois on September 29-30, 1900, made a trip to England. After arrival there he found that there was an <IA_FTS_MATCH>Association</IA_FTS_MATCH> known as The <IA_FTS_MATCH>Commercial Travelers</IA_FTS_MATCH>’ Christian <IA_FTS_MATCH>Association</IA_FTS_MATCH> already in existence."""
        hocr_words = [
            {'text': word}
            for word in text.replace('<IA_FTS_MATCH>', '').replace('</IA_FTS_MATCH>', '').split()
        ]
        match_indices = [(128, 139), (153, 173), (185, 196)]

        assert match_words(hocr_words, match_indices) == [
            [{'text': 'Association'}],
            [
                {'text': 'Commercial'},
                {'text': 'Travelers’'},
            ],
            [{'text': 'Association'}]
        ]

    def test_match_words_adjacent(self):
        from hocr.fts import match_words

        text = """<IA_FTS_MATCH>Hello</IA_FTS_MATCH> <IA_FTS_MATCH>World</IA_FTS_MATCH>"""
        hocr_words = [
            {'text': word}
            for word in text.replace('<IA_FTS_MATCH>', '').replace('</IA_FTS_MATCH>', '').split()
        ]
        match_indices = [(0, 5), (6, 11)]
        assert match_words(hocr_words, match_indices) == [
            [{'text': 'Hello'}],
            [{'text': 'World'}],
        ]
