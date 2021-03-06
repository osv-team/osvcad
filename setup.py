#!/usr/bin/env python
# coding: utf-8

"""setuptools based setup module"""

from setuptools import setup
# from setuptools import find_packages
# To use a consistent encoding
import codecs
from os import path

import osvcad

here = path.abspath(path.dirname(__file__))

# Get the long description from the README_SHORT file
with codecs.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name=osvcad.__name__,
    version=osvcad.__version__,
    description=osvcad.__description__,
    long_description=long_description,
    url=osvcad.__url__,
    download_url=osvcad.__download_url__,
    author=osvcad.__author__,
    author_email=osvcad.__author_email__,
    license=osvcad.__license__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=['OpenCascade', 'PythonOCC', 'ccad', 'CAD', 'parts', 'json'],
    packages=['osvcad',
              'osvcad.jupyter',
              'osvcad.utils',
              'osvcad.ui'],
    install_requires=[],
    # OCC, scipy and wx cannot be installed via pip
    extras_require={'dev': [],
                    'test': ['pytest', 'coverage'], },
    package_data={},
    data_files=[('osvcad/ui/icons',
                 ['osvcad/ui/icons/blue_folder.png',
                  'osvcad/ui/icons/file_icon.png',
                  'osvcad/ui/icons/folder.png',
                  'osvcad/ui/icons/green_folder.png',
                  'osvcad/ui/icons/open.png',
                  'osvcad/ui/icons/python_icon.png',
                  'osvcad/ui/icons/quit.png',
                  'osvcad/ui/icons/refresh.png',
                  'osvcad/ui/icons/save.png']),
                ('osvcad/ui',
                 ['osvcad/ui/osvcad.ico',
                  'osvcad/ui/osvcadui.ini'])],
    entry_points={},
    scripts=['bin/osvcad-ui']
    )
