#!/usr/bin/env python3

from setuptools import setup
from distutils import cmd

import os
import re
import sys

main_py = open(os.path.join('lib', 'urlwatch', '__init__.py')).read()
m = dict(re.findall("\n__([a-z]+)__ = '([^']+)'", main_py))
docs = re.findall('"""(.*?)"""', main_py, re.DOTALL)

if sys.version_info < (3, 3):
    sys.exit('urlwatch requires Python 3.3 or newer')

m['name'] = 'urlwatch'
m['author'], m['author_email'] = re.match(r'(.*) <(.*)>', m['author']).groups()
m['description'], m['long_description'] = docs[0].strip().split('\n\n', 1)
m['install_requires'] = ['minidb', 'PyYAML', 'requests', 'keyring', 'pycodestyle', 'appdirs', 'lxml']
m['scripts'] = ['urlwatch']
m['package_dir'] = {'': 'lib'}
m['packages'] = ['urlwatch']
m['python_requires'] = '>3.3.0'
m['data_files'] = [
    ('share/man/man1', ['share/man/man1/urlwatch.1']),
    ('share/urlwatch/examples', [
        'share/urlwatch/examples/hooks.py.example',
        'share/urlwatch/examples/urls.yaml.example',
    ]),
]


class InstallDependencies(cmd.Command):
    """Install dependencies only"""

    description = 'Only install required packages using pip'
    user_options = []

    def initialize_options(self):
        ...

    def finalize_options(self):
        ...

    def run(self):
        global m
        try:
            from pip._internal import main
        except ImportError:
            from pip import main
        main(['install', '--upgrade'] + m['install_requires'])


m['cmdclass'] = {'install_dependencies': InstallDependencies}

del m['copyright']
setup(**m)
