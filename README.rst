archive-hocr-tools
==================

This repostory contains a python package to ease hocr parsing in a streaming
manner. The library is called ``hocr``.

It also contains various tools:

* ``hocr-combine-stream``: A tool to combine many hocr files into a big hocr
  file. Used internally to combine tesseract per-page results into a larger hocr
  resulting file for an entire book.
* ``hocr-fold-chars``: A tool to transform a per-character hocr file into a
  per-word hocr file.
