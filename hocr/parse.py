import gzip
import re

from lxml import etree

from .util import open_if_required


WRITING_DIRECTION_UNSPECIFIED = 0
WRITING_DIRECTION_LEFT_TO_RIGHT = 1
WRITING_DIRECTION_RIGHT_TO_LEFT = 2
WRITING_DIRECTION_TOP_TO_BOTTOM = 3

wdmap = {
    'ltr': WRITING_DIRECTION_LEFT_TO_RIGHT,
    'rtl': WRITING_DIRECTION_RIGHT_TO_LEFT,
}

BBOX_REGEX = re.compile(r'bbox((\s+-?\d+){4})')
PPI_REGEX = re.compile(r'scan_res((\s+\d+){2})')
BASELINE_REGEX = re.compile(r'baseline((\s+[\d\.\-]+){2})')
X_WCONF_REGEX = re.compile(r'x_wconf((\s+[\d\.\-]+){1})')
X_FSIZE_REGEX = re.compile(r'x_fsize((\s+[\d\.\-]+){1})')


def hocr_page_iterator(fd_or_path):
    """
    Returns an iterator to iterate over a (potentially large) hOCR XML file in a
    streaming manner.

    Args:

    * fd_or_path: open file to operate on, or a path (str).

    Returns:

    * Iterator returning a etree.Element hOCR page.
    """
    fp = open_if_required(fd_or_path)

    # Seek to start
    fp.seek(0)

    # TODO: Add gzip loading, specify what file_like should be (I suggest just
    # file descriptor or just path)
    doc = etree.iterparse(fp, tag='{http://www.w3.org/1999/xhtml}div')
    for act, elem in doc:
        if elem.tag[-3:] == 'div' and elem.attrib['class'] == 'ocr_page':
            page = elem
            yield page

            elem.clear()


def hocr_page_get_dimensions(hocr_page):
    """
    Returns the dimensions (width, height) of a hocr page as returned by
    hocr_page_iterator.

    Args:

    * hocr_page: a page as returned by hocr_page

    Returns:

    * (width, height): tuple of (int, int)
    """
    pagebox = BBOX_REGEX.search(hocr_page.attrib['title']).group(1).split()
    width, height = int(pagebox[2]), int(pagebox[3])
    return width, height


def hocr_page_get_scan_res(hocr_page):
    """
    Returns the X and Y resolution (in DPI) of a hocr page as returned by
    hocr_page_iterator.

    Args:

    * hocr_page: a page as returned by hocr_page

    Returns:

    * (x_res, y_res): tuple of (int, int)

    Or (None, None) if the scan_res property is not present.
    """
    pageppi = PPI_REGEX.search(hocr_page.attrib['title'])
    if pageppi:
        pageppi = pageppi.group(1).split()
        x_res, y_res = int(pageppi[0]), int(pageppi[1])
        return (x_res, y_res)
    else:
        return (None, None)


# XXX: Maybe get rid of scaler here, and just move the normalisation of the
# x_fsize to pdfrenderer.py
def hocr_page_to_word_data(hocr_page, scaler=1):
    """
    Parses a single hocr_page into word data.

    Args:

    * hocr_page: a single hocr_page as returned by hocr_page_iterator
    * (optional) scaler: a scalar to scale font sizes by

    Returns:

    A list of paragraph, each paragraph containing a list of lines, and each
    line containing a list of words, plus properties.

    Paragraphs have the following attributes:

    * `'lines'`: the lines that form this paragraph

    Lines have the following attributes:

    * `'words'`: the words that form this line
    * `'bbox'`: bounding box (tuple of 4 floats)
    * `'baseline'`: baseline of the word (tuple of 2 floats)

    Words have the following attributes:

    * `'text'`: word text, str
    * `'bbox'`: bounding box (tuple of 4 floats)
    * `'fontsize'`: fontsize as a float, or 0.
    * `'writing_direction'`: See WRITING_DIRECTION_* constants
    * `'confidence'`: word confidence, 0 - 100
    """
    paragraphs = []

    for par in hocr_page.xpath('.//*[@class="ocr_par"]'):
        paragraph_data = {'lines': []}

        paragraph_writing_direction = WRITING_DIRECTION_UNSPECIFIED
        if 'dir' in par.attrib:
            paragraph_writing_direction = wdmap[par.attrib['dir']]

        for line in par.getchildren():
            line_data = {}

            linebox = BBOX_REGEX.search(line.attrib['title']).group(1).split()
            baseline = BASELINE_REGEX.search(line.attrib['title'])
            if baseline is not None:
                baseline = baseline.group(1).split()
            else:
                baseline = [0, 0]

            linebox = [float(i) for i in linebox]
            baseline = [float(i) for i in baseline]

            line_data['bbox'] = linebox
            line_data['baseline'] = baseline

            word_data = []
            for word in line.xpath('.//*[@class="ocrx_word"]'):
                rawtext = ''
                wordbased = True
                for char in word.xpath('.//*[@class="ocrx_cinfo"]'):
                    rawtext += char.text
                    wordbased = False

                if wordbased:
                    rawtext = word.text

                box = BBOX_REGEX.search(word.attrib['title']).group(1).split()
                box = [float(i) for i in box]

                conf = int(X_WCONF_REGEX.search(word.attrib['title']).group(1).split()[0])

                f_sizeraw = X_FSIZE_REGEX.search(word.attrib['title'])
                if f_sizeraw:
                    x_fsize = float(f_sizeraw.group(1))
                    x_fsize *= scaler
                else:
                    x_fsize = 0. # Will get fixed later on, in pdfrenderer at least

                writing_direction = WRITING_DIRECTION_UNSPECIFIED
                if 'dir' in word.attrib:
                    writing_direction = wdmap[word.attrib['dir']]
                else:
                    writing_direction = paragraph_writing_direction

                word_data.append({'bbox': box, 'text': rawtext, 'fontsize':
                    x_fsize, 'writing_direction': writing_direction,
                    'confidence': conf})


            line_data['words'] = word_data
            #print('Line words:', word_data)
            paragraph_data['lines'].append(line_data)

        paragraphs.append(paragraph_data)

    return paragraphs


def get_title_attrs(title):
    # Assume Tesseract generated hOCR, where every ';' has a space after it
    sub_title = title.split('; ')
    box = None
    conf = None

    for subt in sub_title:
        if subt[0:7] == 'x_wconf':
            conf = int(subt[8:])
            continue
        if subt[0:4] == 'bbox':
            # TODO: use int()?
            #box = [float(i) for i in subt[i + 5:].split()]
            box = [int(i) for i in subt[5:].split()]
            continue

    return box, conf

def hocr_page_to_word_data_fast(hocr_page):
    """
    Parses a single hocr_page into word data.

    Args:

    * hocr_page: a single hocr_page as returned by hocr_page_iterator

    Returns:

    A list of paragraph, each paragraph containing a list of lines, and each
    line containing a list of words, plus properties.

    Paragraphs have the following attributes:

    * `'lines'`: the lines that form this paragraph

    Lines have the following attributes:

    * `'words'`: the words that form this line

    Words have the following attributes:

    * `'text'`: word text, str
    * `'bbox'`: bounding box (tuple of 4 floats)
    * `'confidence'`: word confidence, 0 - 100
    """
    paragraphs = []

    has_ocrx_cinfo = 0

    for par in hocr_page.xpath('.//*[@class="ocr_par"]'):
        paragraph_data = {'lines': []}

        for line in par.getchildren():
            line_data = {}

            word_data = []
            for word in line.xpath('.//*[@class="ocrx_word"]'):
                title = word.attrib['title']

                box, conf = get_title_attrs(title)

                rawtext = ''
                wordbased = True
                if has_ocrx_cinfo < 2:
                    for char in word.xpath('.//*[@class="ocrx_cinfo"]'):
                        rawtext += char.text
                        wordbased = False
                        has_ocrx_cinfo = 1

                if has_ocrx_cinfo == 0:
                    has_ocrx_cinfo = 2

                if wordbased:
                    rawtext = word.text

                word_data.append({'bbox': box, 'text': rawtext,
                                  'confidence': conf})


            line_data['words'] = word_data
            paragraph_data['lines'].append(line_data)

        paragraphs.append(paragraph_data)

    return paragraphs
