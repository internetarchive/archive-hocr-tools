import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from typing import Dict, List, Tuple, Union
from xml.dom import minidom

import pkg_resources

from .util import roman_to_num

# This becomes the dtb:generator meta in the generated book
content_generator = 'Internet Archive - archive.org'


# TODO: candidate for removal/refactor
def get_metadata_tag_data(metadata: List[Dict[str, str]], tag: str) -> str:
    for el in metadata:
        if el['tag'] == tag:
            return el['text']
    return 'Unknown'


# TODO: candidate for removal/refactor
def tree_to_str(tree: ET.ElementTree, xml_declaration: bool = True) -> bytes:
    return ET.tostring(
        tree.getroot(), encoding='utf-8', xml_declaration=xml_declaration
    )


class DaisyBook:
    def __init__(
        self,
        out_name: str,
        metadata: List[Dict[str, str]],
        content_dir: str = '',
    ) -> None:
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(out_name, 'w')
        self.content_dir = content_dir
        self.book_id = get_metadata_tag_data(metadata, 'identifier')
        self.title = get_metadata_tag_data(metadata, 'title')
        self.author = get_metadata_tag_data(metadata, 'creator')
        self.nav_number = 1

        self.opf_file = self.book_id + '_daisy.opf'

        self.dtbook_file = self.book_id + '_daisy.xml'
        self.dtbook, self.dtbook_book_el = make_dtbook(self.book_id, self.title)

        self.smil_file = self.book_id + '_daisy.smil'
        self.smil, self.smil_seq_el = make_smil(self.book_id)

        self.ncx_file = self.book_id + '_daisy.ncx'
        self.ncx, self.ncx_head_el, self.ncx_navmap_el, self.ncx_pagelist_el = make_ncx(
            self.book_id, self.title, self.author
        )

        self.tag_stack = [self.dtbook_book_el]
        self.navpoint_stack = [self.ncx_navmap_el]

        self.id_index = 1

        self.depth = 0
        self.current_depth = 0
        self.total_page_count = 0
        self.max_page_number = 0

        # style sheet, etc.
        for content in [
            'daisy.css',
            'daisyTransform.xsl',
            'dtbook-2005-3.dtd',
            'html.css',
            'resource.res',
        ]:
            content_src = pkg_resources.resource_filename(
                'hocr', f'daisy/daisy_files/{content}'
            )
            content_str = open(content_src).read()
            self.add(self.content_dir + content, content_str)

        self.manifest_items = [
            {
                'id': 'xml',
                'href': self.dtbook_file,
                'media-type': 'application/x-dtbook+xml',
            },
            {
                'id': 'opf',
                'href': self.book_id + '_daisy.opf',
                'media-type': 'text/xml',
            },
            {
                'id': 'ncx',
                'href': self.ncx_file,
                'media-type': 'application/x-dtbncx+xml',
            },
            {'id': 'smil', 'href': self.smil_file, 'media-type': 'application/smil'},
            {
                'id': 'daisyTransform',
                'href': 'daisyTransform.xsl',
                'media-type': 'text/xsl',
            },
            {'id': 'daisyCss', 'href': 'daisy.css', 'media-type': 'text/css'},
            {'id': 'htmlCss', 'href': 'html.css', 'media-type': 'text/css'},
            {
                'id': 'resource',
                'href': 'resource.res',
                'media-type': 'application/x-dtbresource+xml',
            },
        ]

    def push_tag(
        self,
        tag: str,
        text: str = '',
        attrs: Dict[str, str] = {},
    ) -> str:
        # tag is e.g. frontmatter, bodymatter, rearmatter, level, etc.
        id_str, dtb_el = self.add_tag(tag, text, attrs)
        self.tag_stack.append(dtb_el)
        return id_str

    def pop_tag(self) -> None:
        self.tag_stack.pop()

    def add_tag(
        self,
        tag: str,
        text: str = '',
        attrs: Dict[str, str] = {},
        smil_attrs: Dict[str, str] = {},
    ) -> Tuple[str, ET.Element]:
        id_str = tag + '_' + (str(self.id_index).zfill(5))
        attrs['id'] = id_str
        if text is not None and len(text) > 0:
            smil_attrs.update({'id': id_str, 'class': tag})
            smil_par_el = ET.SubElement(self.smil_seq_el, 'par', smil_attrs)
            ET.SubElement(
                smil_par_el,
                'text',
                {'src': self.dtbook_file + '#' + id_str, 'region': 'textRegion'},
            )
            attrs['smilref'] = self.smil_file + '#' + id_str
        current_dtb_el = self.tag_stack[-1]

        dtb_el = ET.SubElement(current_dtb_el, tag, attrs)
        if text is None:
            print(tag)

        if text is not None and len(text) > 0:
            dtb_el.text = text

        self.id_index += 1
        return id_str, dtb_el

    def add_navpoint(
        self,
        ltag: str,
        htag: str,
        text: str,
    ) -> ET.Element:
        level = str(len(self.navpoint_stack))
        level_id_str = self.push_tag(ltag + level)
        htag_id_str, htag_dtb_el = self.add_tag(
            htag + level, text, smil_attrs={'customTest': 'headerCustomTest'}
        )
        current_navpoint_el = self.navpoint_stack[-1]
        navpoint_el = ET.SubElement(
            current_navpoint_el,
            'navPoint',
            {
                'id': level_id_str,
                'class': 'navpoint-level-level' + level,
                'playOrder': str(self.nav_number),
            },
        )
        navlabel_el = ET.SubElement(navpoint_el, 'navLabel')
        ET.SubElement(navlabel_el, 'text').text = text
        ET.SubElement(
            navpoint_el, 'content', {'src': self.smil_file + '#' + htag_id_str}
        )
        self.nav_number += 1
        return navpoint_el

    def push_navpoint(self, ltag: str, htag: str, text: str) -> None:
        self.current_depth += 1
        if self.current_depth > self.depth:
            self.depth = self.current_depth
        navpoint_el = self.add_navpoint(ltag, htag, text)
        self.navpoint_stack.append(navpoint_el)

    def pop_navpoint(self) -> ET.Element:
        self.current_depth -= 1
        self.pop_tag()
        return self.navpoint_stack.pop()

    def add_pagetarget(self, name: str, value: str, type_: str = 'normal') -> None:
        self.total_page_count += 1

        if isinstance(value, int):
            int_value = value
        elif value.isdigit():
            int_value = int(value)
        elif roman_to_num(value):
            int_value = roman_to_num(value)
        else:
            error_text = (
                "Got non-Arabic, non-Roman numeral, or negative pagetarget value"
            )
            raise ValueError(error_text)

        if int_value > self.max_page_number:
            self.max_page_number = int_value

        pagenum_id, pagenum_el = self.add_tag(
            'pagenum',
            name,
            attrs={'page': type_},
            smil_attrs={'customTest': 'pagenumCustomTest'},
        )
        pagetarget_el = ET.SubElement(
            self.ncx_pagelist_el,
            'pageTarget',
            {
                'id': pagenum_id,
                'value': str(value),
                'type': type_,
                'playOrder': str(self.nav_number),
            },
        )
        navlabel_el = ET.SubElement(pagetarget_el, 'navLabel')
        ET.SubElement(navlabel_el, 'text').text = name
        ET.SubElement(
            pagetarget_el, 'content', {'src': self.smil_file + '#' + pagenum_id}
        )
        self.nav_number += 1

    def add(
        self,
        path: str,
        content_str: Union[bytes, str],
        deflate: bool = True,
    ) -> None:
        info = zipfile.ZipInfo(path)
        info.compress_type = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
        info.external_attr = 0o666 << 16  # fix access
        info.date_time = (
            self.dt.year,
            self.dt.month,
            self.dt.day,
            self.dt.hour,
            self.dt.minute,
            self.dt.second,
        )
        self.z.writestr(info, content_str)

    # TODO: better handle the XML post-processing.
    def finish(self, metadata: List[Dict[str, str]]) -> None:
        root = "<?xml version='1.0' encoding='utf-8'?>\n"

        prefix_xml = (
            root
            + '<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">'
        )
        tree_str = make_opf(metadata, self.manifest_items)
        self.add(self.content_dir + self.opf_file, tree_str)

        metas = [
            {'name': 'dtb:depth', 'content': str(self.depth)},
            {'name': 'dtb:totalPageCount', 'content': str(self.total_page_count)},
            {'name': 'dtb:maxPageNumber', 'content': str(self.max_page_number)},
        ]
        for item in metas:
            ET.SubElement(self.ncx_head_el, 'meta', item)
        prefix_xml = (
            root
            + '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">'
        )
        tree_str = tree_to_str_with_processing(self.ncx, prefix_xml)
        self.add(self.content_dir + self.ncx_file, tree_str)

        doctype = '<!DOCTYPE dtbook SYSTEM "dtbook-2005-3.dtd">\n'
        pi1 = '<?xml-stylesheet type="text/css" href="daisy.css" media="screen"?>\n'
        pi2 = '<?xml-stylesheet type="text/xsl" href="daisyTransform.xsl" media="screen"?>\n'
        prefix_xml = root + doctype + pi1 + pi2
        tree_str = tree_to_str_with_processing(self.dtbook, prefix_xml)
        self.add(self.content_dir + self.dtbook_file, tree_str)

        prefix_xml = (
            root
            + '<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">\n'
        )
        tree_str = tree_to_str_with_processing(self.smil, prefix_xml)
        self.add(self.content_dir + self.smil_file, tree_str)

        self.z.close()


dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'


def make_opf(
    metadata: List[Dict[str, str]], manifest_items: List[Dict[str, str]]
) -> str:
    root_el = ET.Element(
        'package',
        {
            'xmlns': 'http://openebook.org/namespaces/oeb-package/1.0/',
            'unique-identifier': 'bookid',
        },
    )

    metadata_el = ET.SubElement(root_el, 'metadata')
    dc_metadata_el = ET.SubElement(
        metadata_el,
        'dc-metadata',
        {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
            'xmlns:oebpackage': 'http://openebook.org/namespaces/oeb-package/1.0/',
        },
    )

    el = ET.SubElement(dc_metadata_el, 'dc:Format')
    el.text = 'ANSI/NISO Z39.86-2005'

    for md in metadata:
        tagname = md['tag']
        if tagname not in [
            'title',
            'creator',
            'subject',
            'description',
            'publisher',
            'contributor',
            'date',
            'type',
            'format',
            'identifier',
            'source',
            'language',
            'relation',
            'coverage',
            'rights',
        ]:
            continue
        dctag = f'dc:{tagname[:1].upper()}{tagname[1:]}'
        if tagname == 'identifier':
            el = ET.SubElement(dc_metadata_el, dctag, {'id': 'bookid'})
        else:
            el = ET.SubElement(dc_metadata_el, dctag)
        el.text = md['text']

    x_metadata_el = ET.SubElement(metadata_el, 'x-metadata')
    ET.SubElement(
        x_metadata_el, 'meta', {'name': 'dtb:multimediaType', 'content': 'textNCX'}
    )
    ET.SubElement(
        x_metadata_el, 'meta', {'name': 'dtb:multimediaContent', 'content': 'text'}
    )
    ET.SubElement(x_metadata_el, 'meta', {'name': 'dtb:totalTime', 'content': '0'})

    manifest_el = ET.SubElement(root_el, 'manifest')
    for item in manifest_items:
        ET.SubElement(manifest_el, 'item', item)

    spine_el = ET.SubElement(root_el, 'spine')
    ET.SubElement(spine_el, 'itemref', {'idref': 'smil'})

    tree = ET.ElementTree(root_el)
    root = "<?xml version='1.0' encoding='utf-8'?>\n"
    prefix_xml = (
        root
        + '<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">'
    )
    return tree_to_str_with_processing(tree, prefix_xml)


def tree_to_str_with_processing(tree: ET.ElementTree, prefix_xml: str) -> str:
    xml_str = ET.tostring(
        tree.getroot(),
        encoding='unicode',
        method='xml',
    )
    return minidom.parseString(prefix_xml + xml_str).toprettyxml(indent="  ")


def make_dtbook(book_id: str, title: str) -> Tuple[ET.ElementTree, ET.Element]:
    root_el = ET.Element(
        'dtbook',
        {'xmlns': 'http://www.daisy.org/z3986/2005/dtbook/', 'version': '2005-3'},
    )

    head_el = ET.SubElement(root_el, 'head')
    ET.SubElement(head_el, 'meta', {'name': 'dtb:uid', 'content': book_id})
    ET.SubElement(head_el, 'meta', {'name': 'dc:Title', 'content': title})
    book_el = ET.SubElement(root_el, 'book')

    tree = ET.ElementTree(root_el)
    return tree, book_el


def make_smil(book_id: str) -> Tuple[ET.ElementTree, ET.Element]:
    root_el = ET.Element('smil', {'xmlns': 'http://www.w3.org/2001/SMIL20/'})

    head_el = ET.SubElement(root_el, 'head')
    ET.SubElement(head_el, 'meta', {'name': 'dtb:uid', 'content': book_id})
    ET.SubElement(
        head_el, 'meta', {'name': 'dtb:generator', 'content': content_generator}
    )
    ET.SubElement(head_el, 'meta', {'name': 'dtb:totalElapsedTime', 'content': '0'})
    layout_el = ET.SubElement(head_el, 'layout')
    ET.SubElement(
        layout_el,
        'region',
        {
            'id': 'textRegion',
            'fit': 'hidden',
            'showBackground': 'always',
            'height': 'auto',
            'width': 'auto',
            'bottom': 'auto',
            'top': 'auto',
            'left': 'auto',
            'right': 'auto',
        },
    )
    customattributes_el = ET.SubElement(head_el, 'customAttributes')
    ET.SubElement(
        customattributes_el,
        'customTest',
        {'id': 'pagenumCustomTest', 'defaultState': 'false', 'override': 'visible'},
    )
    ET.SubElement(
        customattributes_el,
        'customTest',
        {'id': 'headerCustomTest', 'defaultState': 'false', 'override': 'visible'},
    )

    body_el = ET.SubElement(root_el, 'body')
    seq_el = ET.SubElement(body_el, 'seq', {'id': 'toplevel_seq_id'})
    tree = ET.ElementTree(root_el)
    return tree, seq_el


def make_ncx(
    book_id: str, title: str, author: str
) -> Tuple[ET.ElementTree, ET.Element, ET.Element, ET.Element]:
    root_el = ET.Element(
        'ncx', {'xmlns': 'http://www.daisy.org/z3986/2005/ncx/', 'version': '2005-1'}
    )

    head_el = ET.SubElement(root_el, 'head')
    ET.SubElement(
        head_el,
        'smilCustomTest',
        {
            'id': 'pagenumCustomTest',
            'defaultState': 'false',
            'override': 'visible',
            'bookStruct': 'PAGE_NUMBER',
        },
    )
    ET.SubElement(
        head_el,
        'smilCustomTest',
        {
            'id': 'headerCustomTest',
            'defaultState': 'false',
            'override': 'visible',
            'bookStruct': 'PAGE_NUMBER',
        },
    )
    metas = [
        {'name': 'dtb:uid', 'content': book_id},
        {'name': 'dtb:generator', 'content': content_generator},
    ]
    for item in metas:
        ET.SubElement(head_el, 'meta', item)

    doctitle = ET.SubElement(root_el, 'docTitle')
    ET.SubElement(doctitle, 'text').text = title
    docauthor = ET.SubElement(root_el, 'docAuthor')
    ET.SubElement(docauthor, 'text').text = author

    navmap_el = ET.SubElement(root_el, 'navMap')
    navinfo_el = ET.SubElement(navmap_el, 'navInfo')
    ET.SubElement(navinfo_el, 'text').text = 'Book navigation'

    pagelist_el = ET.SubElement(root_el, 'pageList')
    navlabel_el = ET.SubElement(pagelist_el, 'navLabel')
    ET.SubElement(navlabel_el, 'text').text = 'Pages'

    tree = ET.ElementTree(root_el)
    return tree, head_el, navmap_el, pagelist_el


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
