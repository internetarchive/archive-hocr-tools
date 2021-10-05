from hocr.parse import hocr_page_to_word_data_fast, hocr_page_get_dimensions
from hocr.searching import hocr_lookup_page_by_dat, \
        hocr_lookup_by_plaintext_offset
from hocr.text import get_paragraph_hocr_words, hocr_paragraph_text, \
        get_paragraph_hocr_words

"""
Highly experimental and unstable interface to retrieve page indexes and bounding
boxes for words matching a certain full-text-search query.

Required an external system to perform the highlighting (bin/fts-text-annotate
can serve this purpose)

This API is highly unstable, the code is in need of cleanups, and there likely
isn't a big use for this particular file outside of Internet Archive purposes.
"""

# TODO:
# * Add notes here about internal api, internal code, backwards compat, why the
#   whole thing is so awkward, what search inside does, etc
# * Add documentation to functions, make sure they are also added to sphinx
# * Fixup the poor exception messages, and fixup failing edge cases


# XXX: remove this, we do not need this in production
import re
re_braces = re.compile(r'(\{\{\{|\}\}\})')


# TODO rename and note unstable api
def find_word_boxes(solr_line, hocr_text, hocr_par, page, page_no):
    match_number = 0
    match_with = solr_line
    cur = {
        'text': solr_line,
        'par': []
    }

    results = []

    # TODO: Let's not use regex here, we might not even need this check at all
    if re_braces.sub('', cur['text']) != hocr_text:
        # XXX: Let's not accept mismatches at the moment.
        print('solr_line', repr(solr_line))
        print('hocr_text:', hocr_text)
        print('FAIL2')
        raise Exception('FAIL2')
        #import sys; sys.exit(1)
        cur['error'] = 'mismatch'
        match_number += 1
        results.append((match_number, cur))
        return results

    # Contains a tuple for each match, with the starting and ending rune
    match_indexes = []

    # Match solr_line words to hocr_par words
    # TODO: This needs could be improved some, see below on dealing with
    # match_indexes being empty.
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

        match_indexes.append((rs,
                              re))

    #print('MATCH_INDEXES:', match_indexes)

    if not len(match_indexes):
        # XXX TODO FIXME: This needs to be a hard fail, but let's make it
        # soft fail until I have more time to investigate. Might just need
        # to add +3 to sub_idx for the start and ending case or something.
        return None

    # Get words for this paragraph, so we can match the words against the
    # rune indexes that we know we are interested in. We're going to count
    # the amount of runes in a word (+1 for a space) and do that until we
    # hit a match in match_indexes
    hocr_words = get_paragraph_hocr_words(hocr_par)
    hocr_word_idx = 0

    words = []

    idx = 0
    for (start, end) in match_indexes:
        found = False
        # Fast forward to start using hocr_words
        for word in hocr_words[hocr_word_idx:]:
            wl = len(word['text'] + ' ')
            if idx + wl > start:
                start_word_idx = hocr_word_idx
                hocr_word_idx += 1
                idx += wl
                found = True
                break

            hocr_word_idx += 1
            idx += wl
        if not found:
            # Hard fail if we fail to find the word
            print('FAIL4')
            print(solr_line)
            print(hocr_text)
            raise Exception('FAIL4')
            #import sys; sys.exit(1)

        # Add 3 for {{{. This is in the solr line, but not in our line.
        idx += 3

        found = False
        for word in hocr_words[hocr_word_idx:]:
            wl = len(word['text'] + ' ')
            if idx + wl >= end:
                end_word_idx = hocr_word_idx
                hocr_word_idx += 1
                idx += wl
                found = True
                break

            hocr_word_idx += 1
            idx += wl

        # It is possible our match is the last word, so let's check for
        # that.
        if not found:
            if idx + wl >= end:
                found = True
                end_word_idx = hocr_word_idx

        if not found:
            # Hard fail if we fail to find the word
            print('FAIL4.1')
            print(solr_line)
            print(hocr_text)
            raise Exception('FAIL4.1')
            #import sys; sys.exit(1)

        # Add 3 for }}}. This is in the solr line, but not in our line.
        idx += 3

        #words = hocr_words[start_word_idx:end_word_idx]
        words.extend(hocr_words[start_word_idx:end_word_idx])

        # TODO: sanity check: if search query occurs in the combined text of words

    # boxes is a bounding box for each word, so just translate the hocr ones
    # to what the receiving end expects.
    boxes = []
    for word in words:
        boxes.append({
            'l': word['bbox'][0],
            't': word['bbox'][1],
            'r': word['bbox'][2],
            'b': word['bbox'][3],
        })

    # I am not sure what this bounding box is in the original code, but
    # let's assume it's the box that encompasses all words.
    allword_bboxes = {
        'l': min([x['bbox'][0] for x in words]),
        't': min([x['bbox'][1] for x in words]),
        'r': max([x['bbox'][2] for x in words]),
        'b': max([x['bbox'][3] for x in words]),
    }

    r = allword_bboxes
    page_width, page_height = hocr_page_get_dimensions(page)
    r.update({'page': page_no,
        'boxes': boxes,
        'page_width': page_width,
        'page_height': page_height,
        })
    cur['par'].append(r)

    results.append(cur)
    return results




def find_matches(lookup_table, hocrfp, text):
    text_byte_count = 0
    current_dat = None
    page_number = 0


    for line in text[:-1].split('\n'):
        contains_match = '{{{' in line
        if contains_match:
            contains_match = '}}}' in line

        if contains_match:
            page_number, new_dat = hocr_lookup_by_plaintext_offset(lookup_table,
                    text_byte_count)

            if new_dat != current_dat:
                # Only do this if we're on a new page
                current_dat = new_dat
                page = hocr_lookup_page_by_dat(hocrfp, current_dat)
                paragraphs = hocr_page_to_word_data_fast(page)

            # Figure out what paragraph we are at, based on text length?
            page_start_at = current_dat[0]
            match_at = text_byte_count

            cnt = 0
            match = None

            for idx, paragraph in enumerate(paragraphs):
                txt = hocr_paragraph_text(paragraph)
                cnt += len(txt) + 1 # '\n'

                if page_start_at + cnt > match_at:
                    match = idx
                    break

            if match is None:
                raise Exception('Could not find any match!')

            paragraph = paragraphs[match]
            txt = hocr_paragraph_text(paragraph)

            if txt != line.replace('{{{', '').replace('}}}', ''):
                raise Exception('Reconstructed text does not match:', 'TEXT', txt, 'LINE', line)

            word_results = find_word_boxes(line, txt, paragraph, page,
                                           page_number)
            yield word_results

        if contains_match:
            text_byte_count -= line.count('{{{') * 3
            text_byte_count -= line.count('}}}') * 3
        text_byte_count += len(line) + 1 # '\n'
