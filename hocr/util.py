import gzip

from lxml import etree

#: Contains the HOCR schema
HOCR_SCHEMA = '{http://www.w3.org/1999/xhtml}'


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


def get_header_footer(fd):
    """
    Extract the parts before and after the body elements from a given XML file

    Args:

    * fd: Open file descriptor

    Returns:

    * Tuple (header, footer)
    """
    s = ''
    tags = (HOCR_SCHEMA+'html', HOCR_SCHEMA+'head')
    doc = etree.iterparse(fd, tag=tags, events=('start', 'end'))
    html_elem = None
    head_elem = None

    for act, elem in doc:
        if elem.tag[-4:] == 'html' and act == 'start':
            html_elem = elem
            children = html_elem.getchildren()
            for child in children:
                if child.tag[-4:] == 'body':
                    chs = child.getchildren()
                    for c in chs:
                        child.remove(c)
                    # Remove body, we add an empty one
                    html_elem.remove(child)

        if elem.tag[-4:] == 'head' and act == 'end':
            head_elem = elem
            body_elem = etree.Element('body')

            html_elem.append(head_elem)
            html_elem.append(body_elem)

            s = etree.tostring(html_elem, pretty_print=True, method='xml',
                               encoding='UTF-8', xml_declaration=True)
            s = s.decode('utf-8')
            break

    comp = s.split('<body>')

    # XML-ho
    header = comp[0] + '<body>' + '\n'
    htmlidx = header.find('<html')
    doctype = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'''
    header = header[:htmlidx] + doctype + '\n' + header[htmlidx:]

    footer = comp[1].lstrip()

    return header.encode('utf-8'), footer.encode('utf-8')

