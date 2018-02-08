#!/usr/bin/env python3

from setuptools import setup

import os
import re

main_py = open(os.path.join('lib', 'urlwatch', '__init__.py')).read()
m = dict(re.findall("\n__([a-z]+)__ = '([^']+)'", main_py))
docs = re.findall('"""(.*?)"""', main_py, re.DOTALL)

m['name'] = 'urlwatch'
m['author'], m['author_email'] = re.match(r'(.*) <(.*)>', m['author']).groups()
m['description'], m['long_description'] = docs[0].strip().split('\n\n', 1)
m['download_url'] = '{url}urlwatch-{version}.tar.gz'.format(**m)
m['install_requires'] = ['minidb', 'PyYAML', 'requests', 'keyring', 'pycodestyle', 'appdirs']
m['scripts'] = ['urlwatch']
m['package_dir'] = {'': 'lib'}
m['packages'] = ['urlwatch']
m['data_files'] = [
    ('share/man/man1', ['share/man/man1/urlwatch.1']),
    ('share/urlwatch/examples', [
        'share/urlwatch/examples/hooks.py.example',
        'share/urlwatch/examples/urls.yaml.example',
    ]),
]

del m['copyright']
setup(**m)
