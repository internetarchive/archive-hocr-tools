import gzip
import io
from lxml import etree
from html import escape as html_escape

#: Contains the HOCR schema
HOCR_SCHEMA = '{http://www.w3.org/1999/xhtml}'

def iterparse_tags(fp, tag=None, events=("end",)):
    # fp = io.BytesIO() # test: empty input
    # events is None -> TypeError: 'lxml.etree.HTMLParser' object is not iterable
    assert not events is None
    # use lxml.etree to parse XHTML with HTML entities like "&rarr;"
    doc = etree.iterparse(fp, events=events, tag=tag, html=True)
    try:
        if tag is None:
            for act, elem in doc:
                yield act, elem
        else:
            for act, elem in doc:
                if elem.tag not in tag:
                    continue
                yield act, elem
    except etree.XMLSyntaxError as exc:
        if exc.code == 1:
            # lxml.etree.XMLSyntaxError: no element found
            return
        raise

def elem_tostring(elem, xml_declaration=None, short_empty_elements=False):
    s = etree.tostring(
        elem,
        method="xml",
        encoding="UTF-8",
        xml_declaration=xml_declaration,
        with_tail=False,
        pretty_print=False,
        short_empty_elements=short_empty_elements,
    )
    return s

def elem_inner_text(elem):
    buf = io.StringIO()
    for text in elem.itertext():
        buf.write(text)
    return buf.getvalue()

def elem_inner_html(elem):
    buf = io.StringIO()
    if elem.text:
        buf.write(html_escape(elem.text, quote=False))
    for child in elem:
        # Work on a copy so we don't mutate original tree
        child_bytes = etree.tostring(child, with_tail=False)
        try:
            child_copy = etree.fromstring(child_bytes)
        except etree.XMLSyntaxError as exc:
            # this should never happen...
            raise ValueError(f"failed to parse XML: {child_bytes!r}")
        elem_remove_xmlns(child_copy)
        buf.write(
            etree.tostring(
                child_copy,
                encoding="unicode",
                with_tail=False
            )
        )
        if child.tail:
            buf.write(html_escape(child.tail, quote=False))
    return buf.getvalue()

def elem_remove_xmlns(elem):
    # a: aa<sup xmlns:html="http://www.w3.org/1999/xhtml">bb</sup>cc
    # b: aa<sup>bb</sup>cc
    if isinstance(elem.tag, str):
        elem.tag = etree.QName(elem).localname
    for child in elem:
        elem_remove_xmlns(child)

def open_if_required(fd_or_path):
    """
    Opens a file if `fd_or_path` is a `str`, otherwise returns `fd_or_path`.
    If `fd_or_path` ends with `.gz`, uses `gzip.open`.
    """
    if isinstance(fd_or_path, str):
        if fd_or_path.endswith('.gz'):
            xml_file = gzip.open(fd_or_path, 'rb')
        else:
            xml_file = open(fd_or_path, 'rb')
    else:
        xml_file = fd_or_path

    return xml_file


def get_ocr_system(fd):
    """
    Read the ocr-system meta tag from a new file descriptor containing a hOCR
    document. If you want to use an existing file descriptor, ensure to seek to
    the start first.

    Args:

    * fd: Open file descriptor

    Return:

    * string of the content system or None if none is specified
    """
    header, footer = get_header_footer(fd)

    bio = io.BytesIO()
    bio.write(header + footer)
    bio.seek(0)

    parse = iterparse_tags(bio, tag=(HOCR_SCHEMA+'meta',), events=('end',))
    for (start_end, element) in parse:
        if element.attrib.get('name') == 'ocr-system':
            return element.attrib.get('content')

    return None


def get_header_footer(fd):
    """
    Extract the parts before and after the body elements from a given XML file

    Args:

    * fd: Open file descriptor

    Returns:

    * Tuple (header, footer)
    """
    parser = etree.XMLParser(
        resolve_entities=True,
        recover=True,
        remove_blank_text=False,
    )

    tree = etree.parse(fd, parser)
    root = tree.getroot()

    # Find body
    body = root.find(f".//{XHTML_NS}body")
    if body is None:
        raise ValueError("No <body> element found")

    # Remove all body children
    for child in list(body):
        body.remove(child)

    # Serialize full document
    doc_bytes = etree.tostring(
        tree,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
        short_empty_elements=True,
    )

    s = doc_bytes.decode("utf-8")

    # Split at empty body
    comp = s.split('<body />')

    # XML-ho
    header = comp[0] + '<body>' + '\n'
    htmlidx = header.find('<html')
    doctype = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'''
    header = header[:htmlidx] + doctype + '\n' + header[htmlidx:]

    # Compatibility with previous lxml code - also Tesseract seems inconsistent
    # in this regard
    if '<title />' in header:
        header = header.replace('<title />', '<title></title>')

    footer = '</body>' + comp[1].lstrip()

    return header.encode('utf-8'), footer.encode('utf-8')
