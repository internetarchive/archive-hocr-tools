from setuptools import setup, find_packages
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('hocr/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(name='hocr',
      version=main_ns['__version__'],
      description='hOCR (streaming) parsers and writers',
      author='Merlijn Boris Wolf Wajer',
      author_email='merlijn@archive.org',
      packages=['hocr'],
      scripts=['bin/hocr-combine-stream', 'bin/hocr-fold-chars',
               'bin/hocr-text', 'bin/fts-text-annotate',
               'bin/fts-text-match', 'bin/hocr-lookup-check',
               'bin/hocr-lookup-create', 'bin/hocr-lookup-reconstruct',
               'bin/hocr-text-paragraphs', 'bin/hocr-extract-page',
               'bin/abbyy-to-hocr'],
      include_package_data=True,
      package_data={'hocr': ['data/*']})
