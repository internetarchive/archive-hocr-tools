from io import BytesIO
import os
import sys
import zipfile

from datetime import datetime


from lxml import etree
from lxml.etree import _Element, _ElementTree


# This becomes the dtb:generator meta in the generated book
content_generator = 'Internet Archive - archive.org'

# TODO: candidate for removal/refactor
def get_metadata_tag_data(metadata: list[dict[str, str]], tag: str) -> str:
    for el in metadata:
        if el['tag'] == tag:
            return el['text']
    return 'Unknown'


# TODO: candidate for removal/refactor
def tree_to_str(tree: _Element | _ElementTree, xml_declaration: bool = True) -> bytes:
    return etree.tostring(
        tree, pretty_print=True, xml_declaration=xml_declaration, encoding='utf-8'
    )


class DaisyBook:
    def __init__(
        self,
        out_name: str,
        metadata: list[dict[str, str]],
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
            # TODO: fix pathing.
            content_src = os.path.join(sys.path[0], '../daisy/daisy_files', content)
            content_str = open(content_src).read()
            self.add(self.content_dir + content, content_str)

        self.manifest_items = [
            {
                'id': 'xml',
                'href': self.dtbook_file,
                'media-type': 'application/x-dtbook+xml',
            },
            {'id': 'opf', 'href': self.book_id + '_daisy.opf', 'media-type': 'text/xml'},
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
        attrs: dict[str, str] = {},
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
        attrs: dict[str, str] = {},
        smil_attrs: dict[str, str] = {},
    ) -> tuple[str, _Element]:
        id_str = tag + '_' + (str(self.id_index).zfill(5))
        attrs['id'] = id_str
        # if text is None:
        #     debug()
        if text is not None and len(text) > 0:
            smil_attrs.update({'id': id_str, 'class': tag})
            smil_par_el = etree.SubElement(self.smil_seq_el, 'par', smil_attrs)
            etree.SubElement(
                smil_par_el,
                'text',
                {'src': self.dtbook_file + '#' + id_str, 'region': 'textRegion'},
            )
            attrs['smilref'] = self.smil_file + '#' + id_str
        current_dtb_el = self.tag_stack[-1]

        dtb_el = etree.SubElement(current_dtb_el, tag, attrs)
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
    ) -> _Element:
        level = str(len(self.navpoint_stack))
        level_id_str = self.push_tag(ltag + level)
        htag_id_str, htag_dtb_el = self.add_tag(
            htag + level, text, smil_attrs={'customTest': 'headerCustomTest'}
        )
        current_navpoint_el = self.navpoint_stack[-1]
        navpoint_el = etree.SubElement(
            current_navpoint_el,
            'navPoint',
            {
                'id': level_id_str,
                'class': 'navpoint-level-level' + level,
                'playOrder': str(self.nav_number),
            },
        )
        navlabel_el = etree.SubElement(navpoint_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = text
        etree.SubElement(
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

    def pop_navpoint(self) -> _Element:
        self.current_depth -= 1
        self.pop_tag()
        return self.navpoint_stack.pop()

    def add_pagetarget(self, name, value, type_='normal'):
        self.total_page_count += 1
        if value.isdigit() and isinstance(value, str):
            value = int(value)
        if value > self.max_page_number:
            self.max_page_number = value
        pagenum_id, pagenum_el = self.add_tag(
            'pagenum',
            name,
            attrs={'page': type_},
            smil_attrs={'customTest': 'pagenumCustomTest'},
        )
        pagetarget_el = etree.SubElement(
            self.ncx_pagelist_el,
            'pageTarget',
            {
                'id': pagenum_id,
                'value': str(value),
                'type': type_,
                'playOrder': str(self.nav_number),
            },
        )
        navlabel_el = etree.SubElement(pagetarget_el, 'navLabel')
        etree.SubElement(navlabel_el, 'text').text = name
        etree.SubElement(
            pagetarget_el, 'content', {'src': self.smil_file + '#' + pagenum_id}
        )
        self.nav_number += 1

    def add(
        self,
        path: str,
        content_str: bytes | str,
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

    def finish(self, metadata: list[dict[str, str]]) -> None:
        print(f"{metadata = }")
        tree_str = make_opf(metadata, self.manifest_items)
        self.add(self.content_dir + self.opf_file, tree_str)

        metas = [
            {'name': 'dtb:depth', 'content': str(self.depth)},
            {'name': 'dtb:totalPageCount', 'content': str(self.total_page_count)},
            {'name': 'dtb:maxPageNumber', 'content': str(self.max_page_number)},
        ]
        for item in metas:
            etree.SubElement(self.ncx_head_el, 'meta', item)

        tree_str = tree_to_str(self.ncx)
        self.add(self.content_dir + self.ncx_file, tree_str)

        tree_str = tree_to_str(self.dtbook)
        self.add(self.content_dir + self.dtbook_file, tree_str)

        tree_str = tree_to_str(self.smil)
        self.add(self.content_dir + self.smil_file, tree_str)

        self.z.close()


dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'


def make_opf(
    metadata: list[dict[str, str]],
    manifest_items: list[dict[str, str]],
) -> bytes:
    xml = b"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN"
"http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
unique-identifier="bookid"/>
"""
    tree = etree.parse(BytesIO(xml))
    root_el = tree.getroot()
    metadata_el = etree.SubElement(root_el, 'metadata')
    dc_metadata_el = etree.SubElement(
        metadata_el,
        'dc-metadata',
        nsmap={
            'dc': dc,
            'oebpackage': 'http://openebook.org/namespaces/oeb-package/1.0/',
        },
    )
    el = etree.SubElement(dc_metadata_el, dcb + 'Format')
    el.text = 'ANSI/NISO Z39.86-2005'

    # TODO: ensure required elements: (copy code from epub.py)
    # title
    # publisher
    # date
    # format (must be 'ANSI/NISO Z39.86-2005')
    # language
    # identifier

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
        dctag = dcb + tagname[:1].upper() + tagname[1:]
        if tagname == 'identifier':
            el = etree.SubElement(dc_metadata_el, dctag, {'id': 'bookid'})
            #             el.text = md['text'] + xtra
            el.text = md['text']
        else:
            el = etree.SubElement(dc_metadata_el, dctag)
            el.text = md['text']
    x_metadata_el = etree.SubElement(metadata_el, 'x-metadata')
    el = etree.SubElement(
        x_metadata_el, 'meta', {'name': 'dtb:multimediaType', 'content': 'textNCX'}
    )
    el = etree.SubElement(
        x_metadata_el, 'meta', {'name': 'dtb:multimediaContent', 'content': 'text'}
    )
    el = etree.SubElement(
        x_metadata_el, 'meta', {'name': 'dtb:totalTime', 'content': '0'}
    )

    manifest_el = etree.SubElement(root_el, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest_el, 'item', item)

    spine_el = etree.SubElement(root_el, 'spine')
    etree.SubElement(spine_el, 'itemref', {'idref': 'smil'})

    tree = etree.ElementTree(root_el)
    return tree_to_str(tree)


def make_dtbook(book_id: str, title: str) -> tuple[_ElementTree, _Element]:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dtbook SYSTEM "dtbook-2005-3.dtd">
<dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-3"/>
"""
    tree = etree.parse(BytesIO(xml))
    root_el = tree.getroot()

    # Manually add these, as they seem to get dropped if in parsed xml above.
    pi = etree.ProcessingInstruction(
        'xml-stylesheet', 'type="text/css" href="daisy.css" media="screen"'
    )
    root_el.addprevious(pi)
    pi = etree.ProcessingInstruction(
        'xml-stylesheet', 'type="text/xsl" href="daisyTransform.xsl" media="screen"'
    )
    root_el.addprevious(pi)

    head_el = etree.SubElement(root_el, 'head')
    etree.SubElement(head_el, 'meta', {'name': 'dtb:uid', 'content': book_id})
    etree.SubElement(head_el, 'meta', {'name': 'dc:Title', 'content': title})
    # <book id="book_201979196" xml:space="preserve">
    book_el = etree.SubElement(root_el, 'book')
    return tree, book_el


def make_smil(book_id: str) -> tuple[_ElementTree, _Element]:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">

<smil xmlns="http://www.w3.org/2001/SMIL20/"/>
"""
    tree = etree.parse(BytesIO(xml))
    root_el = tree.getroot()
    head_el = etree.SubElement(root_el, 'head')
    etree.SubElement(head_el, 'meta', {'name': 'dtb:uid', 'content': book_id})
    etree.SubElement(
        head_el, 'meta', {'name': 'dtb:generator', 'content': content_generator}
    )
    etree.SubElement(head_el, 'meta', {'name': 'dtb:totalElapsedTime', 'content': '0'})
    layout_el = etree.SubElement(head_el, 'layout')
    etree.SubElement(
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
    customattributes_el = etree.SubElement(head_el, 'customAttributes')
    etree.SubElement(
        customattributes_el,
        'customTest',
        {'id': 'pagenumCustomTest', 'defaultState': 'false', 'override': 'visible'},
    )
    etree.SubElement(
        customattributes_el,
        'customTest',
        {'id': 'headerCustomTest', 'defaultState': 'false', 'override': 'visible'},
    )

    # 'customAttributes' el = required?
    body_el = etree.SubElement(root_el, 'body')
    seq_el = etree.SubElement(body_el, 'seq', {'id': 'toplevel_seq_id'})
    return tree, seq_el


def make_ncx(
    book_id: str,
    title: str,
    author: str,
) -> tuple[_ElementTree, _Element, _Element, _Element]:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(BytesIO(xml))
    root_el = tree.getroot()
    head_el = etree.SubElement(root_el, 'head')
    etree.SubElement(
        head_el,
        'smilCustomTest',
        {
            'id': 'pagenumCustomTest',
            'defaultState': 'false',
            'override': 'visible',
            'bookStruct': 'PAGE_NUMBER',
        },
    )
    etree.SubElement(
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
        etree.SubElement(head_el, 'meta', item)
    doctitle = etree.SubElement(root_el, 'docTitle')
    etree.SubElement(doctitle, 'text').text = title
    doctitle = etree.SubElement(root_el, 'docAuthor')
    etree.SubElement(doctitle, 'text').text = author

    navmap_el = etree.SubElement(root_el, 'navMap')
    navinfo_el = etree.SubElement(navmap_el, 'navInfo')
    etree.SubElement(navinfo_el, 'text').text = 'Book navigation'

    pagelist_el = etree.SubElement(root_el, 'pageList')
    navlabel_el = etree.SubElement(pagelist_el, 'navLabel')
    etree.SubElement(navlabel_el, 'text').text = 'Pages'

    return tree, head_el, navmap_el, pagelist_el


if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
