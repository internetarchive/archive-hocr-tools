import gzip
import io
from xml.etree import ElementTree

#: Contains the HOCR schema
HOCR_SCHEMA = '{http://www.w3.org/1999/xhtml}'

def register_and_nuke_xhtml_namespace():
    # Nuke the namespace, otherwise it will prefix everything with html:
    ElementTree.register_namespace('', 'http://www.w3.org/1999/xhtml')


def iterparse_tags(fp, tag=None, events=None):
    doc = ElementTree.iterparse(fp, events=events)
    for act, elem in doc:
        if tag is not None and elem.tag not in tag:
            continue

        yield act, elem


def elem_tostring(elem, xml_declaration=None, short_empty_elements=False):
    s = ElementTree.tostring(elem, method='xml',
                             encoding='UTF-8',
                             short_empty_elements=short_empty_elements,
                             xml_declaration=xml_declaration)
    return s

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
    s = ''
    tags = (HOCR_SCHEMA + 'html', HOCR_SCHEMA + 'head')
    doc = iterparse_tags(fd, tag=tags, events=('start', 'end'))
    html_elem = None
    head_elem = None

    for act, elem in doc:
        if elem.tag[-4:] == 'html' and act == 'start':
            html_elem = elem
            children = list(html_elem)
            for child in children:
                if child.tag[-4:] == 'body':
                    chs = list(child)
                    for c in chs:
                        child.remove(c)
                    # Remove body, we add an empty one
                    html_elem.remove(child)

        if elem.tag[-4:] == 'head' and act == 'end':
            head_elem = elem
            body_elem = ElementTree.Element('body')

            html_elem.append(body_elem)

            s = elem_tostring(html_elem, xml_declaration=True,
                              short_empty_elements=True)
            s = s.decode('utf-8')
            break

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
