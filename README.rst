archive-hocr-tools
==================

This repository contains a python package to perform hOCR parsing efficiently,
and it also contains a set of tools that can help perform operations on and
analyse hOCR files.

* ``hocr-combine-stream``: A tool to combine many hocr files into a big hocr
  file while keeping memory usage low. Used internally to combine tesseract
  per-page results into a larger hocr resulting file for an entire book.
* ``hocr-pagenumbers``: A tool to find pagenumbers in multi-page hOCR documents
* ``hocr-fold-chars``: A tool to transform a per-character hocr file into a
  per-word hocr file.
* ``pdf-to-hocr``: A tool to take text content embedded in a PDF, and extract
  it as hOCR format.
* See more tools in the ./bin directory, not all have been documented yet.

The python library is called ``hocr``.
