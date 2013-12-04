#!/usr/bin/env python
# -*- coding: utf8 - *-
"""libunihan lives at <https://github.com/tony/libunihan>.

libunihan
---------

Mass update git, hg and svn repos simultaneously from YAML / JSON file.

"""
import os
import sys
import glob
import urllib
import time
from setuptools import setup
try:
    from urllib import urlretrieve
except:
    from urllib.request import urlretrieve

with open('requirements.pip') as f:
    install_reqs = [line for line in f.read().split('\n') if line]
    tests_reqs = []

if sys.version_info < (2, 7):
    install_reqs += ['argparse']
    tests_reqs += ['unittest2']

import re
VERSIONFILE = "libunihan/__init__.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    __version__ = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

UNIHAN_ZIP = 'http://www.unicode.org/Public/UNIDATA/Unihan.zip'
PACKAGE_DATA = []

thisdir = os.path.join(os.path.dirname(__file__))
datadir = os.path.join(thisdir, './libunihan/data')

if not os.path.exists(datadir):
    os.makedirs(datadir)


def _dl_progress(count, block_size, total_size):
    """
    MIT License: https://github.com/okfn/dpm-old/blob/master/dpm/util.py
    """
    def format_size(bytes):
        if bytes > 1000 * 1000:
            return '%.1fMb' % (bytes / 1000.0 / 1000)
        elif bytes > 10 * 1000:
            return '%iKb' % (bytes / 1000)
        elif bytes > 1000:
            return '%.1fKb' % (bytes / 1000.0)
        else:
            return '%ib' % bytes

    if not count:
        print('Total size: %s' % format_size(total_size))
    last_percent = int((count - 1) * block_size * 100 / total_size)
    # may have downloaded less if count*block_size > total_size
    maxdownloaded = count * block_size
    percent = min(int(maxdownloaded * 100 / total_size), 100)
    if percent > last_percent:
        # TODO: is this acceptable? Do we want to do something nicer?
        sys.stdout.write(
            '%3d%% [%s>%s]\r' % (
                percent,
                percent / 2 * '=',
                (50 - percent / 2) * ' '
            )
        )
        sys.stdout.flush()
    if maxdownloaded >= total_size:
        print('\n')


def save(url, filename):
    urllib.urlretrieve(url, filename, _dl_progress)

if not glob.glob(os.path.join(datadir, 'Unihan*.txt')):
    #urlretrieve(UNIHAN_ZIP, os.path.join(datadir, 'Unihan.zip'))
    save(UNIHAN_ZIP, os.path.join(datadir, 'Unihan.zip'))


setup(
    name='libunihan',
    version=__version__,
    url='http://github.com/tony/libunihan/',
    download_url='https://pypi.python.org/pypi/libunihan',
    license='BSD',
    author='Tony Narlock',
    author_email='tony@git-pull.com',
    description='Unihan abstraction layer.',
    long_description=open('README.rst').read(),
    include_package_data=True,
    install_requires=install_reqs,
    tests_require=tests_reqs,
    test_suite='libunihan.testsuite',
    zip_safe=False,
    packages=['libunihan', 'libunihan.testsuite'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        "License :: OSI Approved :: BSD License",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
)