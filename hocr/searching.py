import json

from lxml import etree

from .parse import hocr_page_iterator
from .text import hocr_get_xml_page_offsets, hocr_get_plaintext_page_offsets, \
        hocr_page_text

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


def hocr_lookup_page_by_plaintext_offset(fp, page_lookup_data, pos_bytes_plain):
    """
    Get the XML for a specific hOCR page that corresponds to the plaintext
    offset as specified in pos_bytes_plain.

    Args:

    * fp
    * page_lookup_data: Lookup table as returned by hocr_load_lookup_table or
      hocr_get_page_lookup_table.
    * pos_bytes_plain: Offset in plaintext of the hOCR file.
    """
    for dat in page_lookup_data:
        tstart, tend = dat[0:2]
        xstart, xend = dat[2:4]

        if tstart <= pos_bytes_plain <= tend:
            fp.seek(xstart)
            xml = fp.read(xend-xstart)
            root = etree.fromstring(xml)
            return root

    return None


def hocr_load_lookup_table(path):
    """
    Load lookup table from JSON.

    Args:

    * path: Path to JSON 
    
    Returns:

    * Lookup table
    """
    return json.load(open(path, 'r'))



def hocr_save_lookup_table(lookup_table, path):
    """
    Save lookup table to JSON.

    Args:

    * lookup_table: Lookup table as returned by hocr_get_page_lookup_table
    * path: Path to save to
    """
    json.dump(lookup_table, open(path, 'w+'))


def hocr_get_fts_text(fd_or_path):
    """
    """
    for page in hocr_page_iterator(fd_or_path):
        yield hocr_page_text(page)
