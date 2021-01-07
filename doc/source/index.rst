.. archive-hocr-tools documentation master file, created by
   sphinx-quickstart on Thu Jan  7 16:12:28 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to archive-hocr-tools's documentation!
==============================================

Usage
-----


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
