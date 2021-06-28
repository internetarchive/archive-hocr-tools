import json

from lxml import etree

from .util import open_if_required
from .parse import hocr_page_iterator, hocr_page_to_word_data_fast
from .text import hocr_get_xml_page_offsets, hocr_get_plaintext_page_offsets, \
        hocr_page_text_from_word_data, get_paragraph_hocr_words


def hocr_get_page_lookup_table(fd_or_path):
    """
    Create lookup table for a given hOCR document. This allows for quickly
    jumping to specific XML pages.

    Args:

    * fd_or_path: file descriptor or filepath to the hOCR file

    Returns:

    Lookup table (list of a list) with each list entry:

    * [text_start_byte, text_end_byte, xml_start_byte, xml_end_byte]
    """
    text_ranges = hocr_get_plaintext_page_offsets(fd_or_path)
    xml_ranges = hocr_get_xml_page_offsets(fd_or_path)

    if len(text_ranges) != len(xml_ranges):
        # Perhaps use something other than ValueError
        raise ValueError('text_ranges and xml_ranges do not match')

    res = []
    for text, xml in zip(text_ranges, xml_ranges):
        res.append((text[0], text[1], xml[0], xml[1]))

    return res

def hocr_lookup_by_plaintext_offset(page_lookup_data, pos_bytes_plain):
    """
    Get the lookup index and data for a page that corresponds to the plaintext
    offset as
    specified in pos_bytes_plain.

    Args:

    * page_lookup_data: Lookup table as returned by hocr_load_lookup_table or
      hocr_get_page_lookup_table.
    * pos_bytes_plain: Offset in plaintext of the hOCR file.
    """
    for idx, dat in enumerate(page_lookup_data):
        tstart, tend = dat[0:2]
        xstart, xend = dat[2:4]

        if tstart <= pos_bytes_plain < tend:
            return idx, dat

    return None, None


def hocr_lookup_page_by_dat(fp, dat):
    """
    Get the XML for a specific hOCR page that corresponds to the lookup
    data `dat`.

    Args:

    * fp: file pointer to hOCR file
    * `dat`: lookup table entry for the page
    """
    xstart, xend = dat[2:4]

    fp.seek(xstart)
    xml = fp.read(xend-xstart)
    root = etree.fromstring(xml)
    return root


def hocr_lookup_page_by_plaintext_offset(fp, page_lookup_data, pos_bytes_plain):
    """
    Get the XML for a specific hOCR page that corresponds to the plaintext
    offset as specified in pos_bytes_plain.

    Args:

    * fp: file pointer to hOCR file
    * page_lookup_data: Lookup table as returned by hocr_load_lookup_table or
      hocr_get_page_lookup_table.
    * pos_bytes_plain: Offset in plaintext of the hOCR file.
    """
    _, dat = hocr_lookup_by_plaintext_offset(page_lookup_data, pos_bytes_plain)
    return hocr_lookup_page_by_dat(fp, dat)


def hocr_load_lookup_table(path):
    """
    Load lookup table from JSON.

    Args:

    * fd_or_path: File to load from
    
    Returns:

    * Lookup table
    """
    fp = open_if_required(path)
    return json.loads(fp.read().decode('utf-8'))


def hocr_save_lookup_table(lookup_table, fd_or_path):
    """
    Save lookup table to JSON.

    Args:

    * lookup_table: Lookup table as returned by hocr_get_page_lookup_table
    * fd_or_path: File to save to
    """
    if isinstance(fd_or_path, str):
        fd_or_path = open(fd_or_path, 'w+')
    json.dump(lookup_table, fd_or_path)


def hocr_get_fts_text(fd_or_path):
    """
    Return text that can be ingested in a full text search engine like SOLR or
    Elastic.

    Args:

    * fd_or_path: File descriptor or path to hOCR file

    Returns:

    Repeatedly yields a tuple of (``str``, ``list of int``),
    page text and a list of word confidences on the page.
    """
    for page in hocr_page_iterator(fd_or_path):
        word_data = hocr_page_to_word_data_fast(page)
        page_text = hocr_page_text_from_word_data(word_data)

        confs = []
        for paragraph in word_data:
            confs += [x['confidence'] for x in get_paragraph_hocr_words(paragraph)]

        yield page_text, confs
