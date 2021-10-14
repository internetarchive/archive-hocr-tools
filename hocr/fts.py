from hocr.parse import hocr_page_to_word_data_fast, hocr_page_get_dimensions
from hocr.searching import hocr_lookup_page_by_dat, \
        hocr_lookup_by_plaintext_offset
from hocr.text import get_paragraph_hocr_words, hocr_paragraph_text, \
        get_paragraph_hocr_words, hocr_page_text_from_word_data

"""
Highly experimental and unstable interface to retrieve page indexes and
bounding boxes for words matching a certain full-text-search query.

Required an external system to perform the highlighting (bin/fts-text-annotate
can serve this purpose).

This API is highly unstable, the code is in need of cleanups, and there likely
isn't a big use for this particular file outside of Internet Archive purposes,
unless you want to match ElasticSearch highlighted plaintext to hOCR pages to
get the text coordinates of the matches.
"""


def match_words(hocr_words, match_indexes):
    def m(match, word_start, word_end):
        # XXX: We might need to turn some of these <= into < or so, there could
        # be an off-by-one error here, matching a next word when it should not.
        return (match[0] >= word_start and match[0] <= word_end) or \
               (match[1] >= word_start and match[1] <= word_end) or \
               (word_start >= match[0] and word_end <= match[0]) or \
               (word_start >= match[1] and word_end <= match[1])

    matching_words = []
    in_word = False
    current_match_words = []

    current_match_index = 0
    str_idx = 0

    for word in hocr_words:
        if current_match_index >= len(match_indexes):
            break

        word_start = str_idx
        word_end = str_idx + len(word['text'])

        if in_word:
            # match in the word, or word in match
            if m(match_indexes[current_match_index], word_start, word_end):
                current_match_words.append(word)
            else:
                matching_words.append(current_match_words)
                current_match_words = []
                current_match_index += 1
                in_word = False

        if not in_word and current_match_index < len(match_indexes):
            if m(match_indexes[current_match_index], word_start, word_end):
                current_match_words.append(word)

                in_word = True

        # Add + 1 for the space after a word
        str_idx += len(word['text']) + 1

    if current_match_index < len(match_indexes):
        word_start = str_idx
        word_end = str_idx + len(word['text'])

        if in_word:
            if m(match_indexes[current_match_index], word_start, word_end):
                current_match_words.append(word)
            else:
                matching_words.append(current_match_words)
                current_match_words = []
                current_match_index += 1
                in_word = False
        else:
            if m(match_indexes[current_match_index], word_start, word_end):
                current_match_words.append(word)
                matching_words.append(current_match_words)

    return matching_words


def find_word_boxes(solr_line, hocr_text, hocr_par, page, page_no):
    match_number = 0
    match_with = solr_line
    cur = {
        'text': solr_line,
        'par': []
    }

    results = []

    # Contains a tuple for each match, with the starting and ending rune
    match_indexes = []

    # Match solr_line words to hocr_par words
    sub_idx = 0
    while True:
        s = solr_line[sub_idx:].find('{{{')
        if s == -1:
            break
        rs = s + sub_idx + 3

        sub_idx += s
        e = solr_line[sub_idx:].find('}}}')
        if e == -1:
            break
        re = e + sub_idx
        sub_idx += e

        match_indexes.append((rs, re))

    # Normalise indices for string without {{{ and }}}, this makes life easier
    # later on
    for idx in range(len(match_indexes)):
        rs, re = match_indexes[idx]
        match_indexes[idx] = (rs - 6 * (idx) - 3, re - 6 * (idx) - 3)

    if not len(match_indexes):
        if solr_line.find('}}}') < solr_line.find('{{{'):
            # XXX: Known bug, this happens because elastic currently matches
            # across paragraph boundaries, which we do not support. We could
            # extend our match to support multi-paragraph matching, but we're
            # probably going to change our elastic search to not match across
            # paragraphs or even pages.
            pass
        else:
            raise Exception('No match_indexes for %s' % repr(solr_line))

        return None

    # Now we know where our matches are in the text (without the brackets), we
    # need to match that to the hocr words, because just knowing which text is
    # not relevant - we need to find the bounding boxes for the matching text.
    hocr_words = get_paragraph_hocr_words(hocr_par)
    word_matches = match_words(hocr_words, match_indexes)

    # We have bounding boxes per word, but the current API doesn't permit us to
    # pass multiple bounding boxes for a single match, so let's find the
    # encompassing bounding box
    boxes = []
    for words in word_matches:
        boxes.append({
            'l': min([x['bbox'][0] for x in words]),
            't': min([x['bbox'][1] for x in words]),
            'r': max([x['bbox'][2] for x in words]),
            'b': max([x['bbox'][3] for x in words]),
            'page': page_no,
        })

    left = None
    top = None
    right = None
    bottom = None
    for box in boxes:
        if left is None:
            left = box['l']
        else:
            left = min(left, box['l'])

        if top is None:
            top = box['t']
        else:
            top = min(top, box['t'])

        if right is None:
            right = box['r']
        else:
            right = max(right, box['r'])

        if bottom is None:
            bottom = box['b']
        else:
            bottom = max(bottom, box['b'])
    all_boxes = {'l': left, 't': top, 'r': right, 'b': bottom}

    r = all_boxes
    page_width, page_height = hocr_page_get_dimensions(page)
    r.update({'page': page_no,
              'boxes': boxes,
              'page_width': page_width,
              'page_height': page_height})

    cur['par'].append(r)

    results.append(cur)
    return results


def find_matches(lookup_table, hocrfp, text, es_whitespace_fixup_required=False):
    text_byte_count = 0
    current_dat = None
    page_number = 0

    if es_whitespace_fixup_required:
        # There might be faster ways of doing this (e.g. read the _searchtext
        # file and count the amount of 'whitespace' bytes)
        done = False
        for dat in lookup_table:
            page = hocr_lookup_page_by_dat(hocrfp, dat)
            word_data = hocr_page_to_word_data_fast(page)
            page_text = hocr_page_text_from_word_data(word_data)

            for line in page_text:
                if line.strip() == '':
                    # Add counted bytes, one for newline
                    text_byte_count += len(line) + 1
                    continue
                else:
                    done = True
                    break
            if done:
                break


    # For every line in the highlighted text, let's find matches...
    for line in text[:-1].split('\n'):
        # Line should contain both '{{{' and '}}}'
        contains_left_match = '{{{' in line
        contains_right_match = '}}}' in line

        contains_match = contains_left_match and contains_right_match

        if contains_left_match or contains_right_match and not contains_match:
            # Matches span multiple lines...
            pass

        if contains_match:
            page_number, new_dat = \
                    hocr_lookup_by_plaintext_offset(lookup_table,
                                                    text_byte_count)

            # Check if we need to change/reload our page and paragraphs
            # variables
            if new_dat != current_dat:
                # Only do this if we're on a new page
                current_dat = new_dat
                page = hocr_lookup_page_by_dat(hocrfp, current_dat)
                paragraphs = hocr_page_to_word_data_fast(page)

            # Figure out what paragraph we are at, based on text length?
            # Find paragraph that contains this line, we know where the line
            # starts, so now we just need to find the paragraph, we can do this
            # with getting the paragraph text on a page, and add the amount of
            # characters, until we reach the line start.
            page_start_at = current_dat[0]
            match_at = text_byte_count
            cnt = 0
            match = None
            for idx, paragraph in enumerate(paragraphs):
                txt = hocr_paragraph_text(paragraph)
                # Add + 1 for newline
                cnt += len(txt) + 1

                if page_start_at + cnt > match_at:
                    match = idx
                    break

            if match is None:
                # This should never happen
                raise Exception('Could not find any match!')

            paragraph_words = paragraphs[match]
            paragraph_txt = hocr_paragraph_text(paragraph_words)

            # TODO: We might want to remove this in the future, it's wasteful
            # to do the replace again.
            if paragraph_txt != line.replace('{{{', '').replace('}}}', ''):
                raise Exception('Reconstructed text does not match')

            word_results = find_word_boxes(line, paragraph_txt,
                                           paragraph_words, page, page_number)

            # We currently (rarely) allow word_results to be empty.
            # This happens for example in a paragraph like this:
            # " THE}}} CAMP OF {{{THE BRITISH MISSION AT ADOWA. From a Drawing by F. VILLIERs.  the}}}"
            # where elastic finds very strange matches and also across
            # paragraph, which we do not support. this is also special cased in
            # find_word_boxes
            if word_results is not None:
                yield word_results

        # Correct for any {{{ and }}}, which are not in our plaintext, but are
        # in the FTS text
        subtract = 0
        if contains_left_match:
            subtract += line.count('{{{') * 3
        if contains_right_match:
            subtract += line.count('}}}') * 3

        # Add counted bytes, plus one for the newline
        text_byte_count += len(line) - subtract + 1
