import gzip

from lxml import etree
import re


WRITING_DIRECTION_UNSPECIFIED = 0
WRITING_DIRECTION_LEFT_TO_RIGHT = 1
WRITING_DIRECTION_RIGHT_TO_LEFT = 2
WRITING_DIRECTION_TOP_TO_BOTTOM = 3

wdmap = {
    'ltr': WRITING_DIRECTION_LEFT_TO_RIGHT,
    'rtl': WRITING_DIRECTION_RIGHT_TO_LEFT,
}

BBOX_REGEX = re.compile(r'bbox((\s+\d+){4})')
BASELINE_REGEX = re.compile(r'baseline((\s+[\d\.\-]+){2})')
X_WCONF_REGEX = re.compile(r'x_wconf((\s+[\d\.\-]+){1})')
X_SIZE_REGEX = re.compile(r'x_size((\s+[\d\.\-]+){1})')
X_FSIZE_REGEX = re.compile(r'x_fsize((\s+[\d\.\-]+){1})')

def hocr_page_iterator(file_path):
    """
    Returns an iterator to iterate over a (potentially large) hOCR XML file in a
    streaming manner.

    Args:
    * file_path (str): Path to hocr file (if gzip, will get decompressed on the
                       fly)

    Returns:
    Iterator returning a etree.Element of the page.
    """
    if file_path.endswith('.gz'):
        fp = gzip.open(file_path)
    else:
        fp = open(file_path, 'rb')
    #
    # TODO: Add gzip loading, specify what file_like should be (I suggest just
    # file descriptor or just path)
    doc = etree.iterparse(fp)
    for act, elem in doc:
        if elem.tag[-3:] == 'div' and elem.attrib['class'] == 'ocr_page':
            page = elem
            yield page

            elem.clear()

# TODO: Check if the one in archive-pdf-tools pdfrenderer.py is more up to date
# XXX: Maybe get rid of scaler here, and just move the normalisation of the
# x_fsize to pdfrenderer.py
def hocr_page_to_word_data(hocr_page, scaler=1):
    """
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
                # XXX: if no ocrx_cinfo, then just read word.text
                rawtext = ''
                for char in word.xpath('.//*[@class="ocrx_cinfo"]'):
                    rawtext += char.text

                box = BBOX_REGEX.search(word.attrib['title']).group(1).split()
                box = [float(i) for i in box]

                conf = int(X_WCONF_REGEX.search(word.attrib['title']).group(1).split()[0])

                f_sizeraw = X_FSIZE_REGEX.search(word.attrib['title'])
                if f_sizeraw:
                    x_fsize = float(f_sizeraw.group(1))
                    x_fsize *= scaler
                else:
                    x_fsize = 0. # Will get fixed later on

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
