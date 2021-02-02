import pytest
import requests


@pytest.fixture(scope='session')
def sim_hocr_file(tmp_path_factory):
    hocr = tmp_path_factory.getbasetemp() / 'sim_english-illustrated-magazine_1884-12_2_15_chocr.html.gz'
    #hocr = tmp_path_factory.getbasetemp() / 'sim_english-illustrated-magazine_1884-12_2_15_hocr.html.gz'

    url = 'https://archive.org/download/sim_english-illustrated-magazine_1884-12_2_15/sim_english-illustrated-magazine_1884-12_2_15_chocr.html.gz'
    #url = 'https://archive.org/download/sim_english-illustrated-magazine_1884-12_2_15/sim_english-illustrated-magazine_1884-12_2_15_hocr.html.gz'

    r = requests.get(url)

    hocr.write_bytes(r.content)

    return hocr
