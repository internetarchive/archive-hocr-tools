from setuptools import setup, find_packages
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('hocr/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

version = main_ns['__version__']
setup(name='archive-hocr-tools',
      version=version,
      packages=['hocr'],
      description='hOCR (streaming) parsers and writers',
      author='Merlijn Boris Wolf Wajer',
      author_email='merlijn@archive.org',
      url='https://github.com/internetarchive/archive-hocr-tools',
      download_url='https://github.com/internetarchive/archive-hocr-tools/archive/%s.tar.gz' % version,
      keywords=['hOCR', 'Internet Archive'],
      license='AGPL-3.0',
      scripts=['bin/hocr-combine-stream', 'bin/hocr-fold-chars',
               'bin/hocr-text', 'bin/fts-text-annotate',
               'bin/fts-text-match', 'bin/hocr-lookup-check',
               'bin/hocr-lookup-create', 'bin/hocr-lookup-reconstruct',
               'bin/hocr-text-paragraphs', 'bin/hocr-extract-page',
               'bin/abbyy-to-hocr', 'bin/hocr-split-pages',
               'bin/hocr-flatten-pages', 'bin/hocr-confidence-filter',
               'bin/hocr-to-epub', 'bin/pdf-to-hocr',
               'bin/hocr-pagenumbers', 'bin/hocr-to-daisy'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Programming Language :: Python :: 3',
      ],
      python_requires='>=3.6',
      include_package_data=True,
      install_requires=[],
      extras_require={
          'daisy': ['iso639==0.1.4'],
          'epub': ['ebooklib==0.17.1', 'internetarchive-deriver-module==1.0.1', 'iso639==0.1.4'],
          'pdf': ['PyMuPDF==1.22.5', 'numpy==1.21.3'],
          'pagenumber': ['viterbi-trellis==0.0.3', 'roman>=3.3', 'numpy>=1.21.3', 'scikit-learn>=1.2.2'],
      },
      package_data={'hocr': ['data/*', 'daisy/*']})
