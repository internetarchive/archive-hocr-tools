import pytest
from os.path import join

def read_file(tmp_path_factory, n):
    data = tmp_path_factory.getbasetemp() / n
    with open(join('test-files', n), 'rb') as fp:
        data.write_bytes(fp.read())
    return data

@pytest.fixture(scope='session')
def sim_hocr_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'sim_english-illustrated-magazine_1884-12_2_15_chocr.html.gz')

@pytest.fixture(scope='session')
def pdf_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'test_arlington_heights_daily_herald-19760903.pdf')

@pytest.fixture(scope='session')
def pdf_metadata_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'test_arlington_heights_daily_herald-19760903_pdfmeta.json')

@pytest.fixture(scope='session')
def pdf_chocr_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'test_arlington_heights_daily_herald-19760903_chocr.html')

@pytest.fixture(scope='session')
def sim_english_pagenumber_json_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'sim_english_pagenumbers.json')

@pytest.fixture(scope='session')
def abbyy_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'sim_english-illustrated-magazine_1884-12_2_15_abbyy')

@pytest.fixture(scope='session')
def abbyy_to_hocr_file(tmp_path_factory):
    return read_file(tmp_path_factory, 'sim_english-abbyy-to-hocr-result.html')
