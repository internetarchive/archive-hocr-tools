.. archive-hocr-tools documentation master file, created by
   sphinx-quickstart on Thu Jan  7 16:12:28 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to archive-hocr-tools's documentation!
==============================================

Tools Usage
-----------


hocr-combine-stream
~~~~~~~~~~~~~~~~~~~

Tool to combine several hOCR files into a single hOCR file.
Works in a streaming mode, so has a low memory footprint regardless of input
file size.

Usage::

    hocr-combine-stream -g 'hocr-page-*.html' > hocr-combined.html


hocr-fold-chars
~~~~~~~~~~~~~~~

Convert a character-based hOCR file (with ``ocrx_cinfo`` entries) into a
word-based hOCR file with ``ocrx_word`` entries. This can be useful if you don't
care about per-character information and wish to decrease the file size to
increase throughput (network or computational).


Usage::

    hocr-fold-chars -f hocr-with-characters.html > hocr-with-words.html

hocr-text
~~~~~~~~~

Creates a text-only version of a hOCR file. Discards words if they are below a
certain (currently hardcoded) confidence level. Can be used to turn hOCR files
into large text files for ingestion into full text search engines, or just to
quickly read or search-for text.

Usage::

    hocr-text -f hocr-file.html > hocr-plain.txt


hocr-lookup-create
~~~~~~~~~~~~~~~~~~

Creates a "lookup table" that maps the start and end of pages (in both plaintext
and XML). Can be used to quickly parse only a subset of a big hOCR file. Text
offsets are as `hocr-text`_ would report them (also discarding certain words
with the same hardcoded confidence level).

Can be used in combination with `fts-text-match`_ to quickly highlight matches
from a FTS engine.

Usage::

    hocr-lookup-create -f hocr-file.html > hocr-file-lookup.json


Searching tools
~~~~~~~~~~~~~~~

fts-text-annotate
~~~~~~~~~~~~~~~~~

Annotates a plain-text file as produced by `hocr-text`_ with ``{{{`` and
``}}}`` around matching text. Resulting file can be used as input for
`fts-text-match`_.

Usage::

    fts-text-annotate -f hocr-plain.txt -p textbooks > hocr-plain-hl.txt


fts-text-match
~~~~~~~~~~~~~~

Finds matches given a hOCR file, a highlighted plaintext file (per
`fts-text-annotate`_) and a lookup table (per `hocr-lookup-create`_).

Matches are reported (including word bounds) to standard out, as `JSON lines
<https://jsonlines.org/>`_.

Usage::

    fts-text-match --hocr hocr-file.html --annotated-text hocr-plain-hl.txt --table hocr-file-lookup.json


Testing tools
-------------



TDB:

* hocr-text-paragraphs
* hocr-lookup-check
* hocr-lookup-reconstruct




Library usage
-------------


Print all words in a hOCR file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a hOCR file and get all the word information for each page::

    hocr_iter = hocr_page_iterator('test_hocr.html.gz')
    for page in hocr_iter:
        w, h = hocr_page_get_dimensions(page)
        word_data = hocr_page_to_word_data(page)

        for paragraph in word_data:
            for line in paragraph['lines']:
                for word in line['words']:
                    print(word['text'], word['bbox'])


Create a lookup table for a hOCR file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    import sys
    filename = sys.argv[1]

    # Build lookup table
    page_info = hocr_get_page_lookup_table(filename)
    # Find the last page in the document, take the plain text start byte and
    # subtract one, to get to the second last page of the document
    second_last_page = page_info[-1][0]-1
    page = hocr_lookup_page_by_plaintext_offset(f, page_info, second_last_page)
    txt = hocr_page_text(page)
    print('Text', txt)


Components
----------

.. toctree::
   :maxdepth: 2
   :caption: Sections:

   parse.rst
   text.rst
   searching.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
