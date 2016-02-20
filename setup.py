#!/usr/bin/python
# -*- coding: utf-8 -*-
# Minimalistic, automatic setup.py file for Python modules
# Copyright (c) 2008-2016 Thomas Perl <thp.io/about>

from setuptools import setup

import os
import re

PACKAGE_NAME = 'urlwatch'
DEPENDENCIES = ['minidb', 'PyYAML', 'requests']
HERE = os.path.dirname(__file__)

# Assumptions:
#  1. Package name equals main script file name (and only one script)
#  2. Main script contains docstring + dunder-{author, license, url, version}
#  3. Data files are in "share/", will be installed in $(PREFIX)/share
#  4. Packages are in "lib/", no modules

main_py = open(os.path.join(HERE, 'lib', PACKAGE_NAME, '__init__.py')).read()
m = dict(re.findall("\n__([a-z]+)__ = '([^']+)'", main_py))
docs = re.findall('"""(.*?)"""', main_py, re.DOTALL)

m['name'] = PACKAGE_NAME
m['author'], m['author_email'] = re.match(r'(.*) <(.*)>', m['author']).groups()
m['description'], m['long_description'] = docs[0].strip().split('\n\n', 1)
m['download_url'] = m['url'] + PACKAGE_NAME + '-' + m['version'] + '.tar.gz'

m['scripts'] = [os.path.join(HERE, PACKAGE_NAME)]
m['package_dir'] = {'': os.path.join(HERE, 'lib')}
m['packages'] = ['.'.join(dirname[len(HERE)+1:].split(os.sep)[1:])
                 for dirname, _, files in os.walk(os.path.join(HERE, 'lib')) if '__init__.py' in files]
m['data_files'] = [(dirname[len(HERE)+1:], [os.path.join(dirname[len(HERE)+1:], fn) for fn in files])
                   for dirname, _, files in os.walk(os.path.join(HERE, 'share')) if files]
m['install_requires'] = DEPENDENCIES

setup(**m)
