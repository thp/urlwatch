#!/usr/bin/env python3

from setuptools import setup

import os
import re
import sys

with open(os.path.join('lib', 'urlwatch', '__init__.py')) as f:
    main_py = f.read()
m = dict(re.findall("\n__([a-z]+)__ = '([^']+)'", main_py))
docs = re.findall('"""(.*?)"""', main_py, re.DOTALL)

if sys.version_info < (3, 7):
    sys.exit('urlwatch requires Python 3.7 or newer')

m['name'] = 'urlwatch'
m['author'], m['author_email'] = re.match(r'(.*) <(.*)>', m['author']).groups()
m['description'], m['long_description'] = docs[0].strip().split('\n\n', 1)
m['install_requires'] = ['minidb>=2.0.6', 'PyYAML', 'requests', 'keyring', 'appdirs', 'lxml', 'cssselect']
if sys.platform == 'win32':
    m['install_requires'].extend(['colorama'])
m['entry_points'] = {"console_scripts": ["urlwatch=urlwatch.cli:main"]}
m['package_dir'] = {'': 'lib'}
m['packages'] = ['urlwatch']
m['python_requires'] = '>=3.6'
m['data_files'] = [
    ('share/man/man1', [
        'share/man/man1/urlwatch.1',
    ]),
    ('share/man/man5', [
        'share/man/man5/urlwatch-config.5',
        'share/man/man5/urlwatch-filters.5',
        'share/man/man5/urlwatch-jobs.5',
        'share/man/man5/urlwatch-reporters.5',
    ]),
    ('share/man/man7', [
        'share/man/man7/urlwatch-cookbook.7',
        'share/man/man7/urlwatch-deprecated.7',
        'share/man/man7/urlwatch-intro.7',
    ]),
    ('share/urlwatch/examples', [
        'share/urlwatch/examples/hooks.py.example',
        'share/urlwatch/examples/urls.yaml.example',
    ]),
]
m['project_urls'] = {
    'Source': 'https://github.com/thp/urlwatch',
    'Tracker': 'https://github.com/thp/urlwatch/issues',
}

del m['copyright']
setup(**m)
