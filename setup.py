#!/usr/bin/python

from distutils.core import setup

import os
import os.path
import glob
import imp

package = 'urlwatch'
script = 'urlwatch'

# get program info from urlwatch module
s = imp.load_source('s', script)
# remove dummy file created by imp.load_source
os.unlink(script+'c')

setup(
        name = s.pkgname,
        description = s.__doc__,
        version = s.__version__,
        author = s.__author__, # FIXME: name only
        # FIXME: author_email
        url = s.__homepage__,
        scripts = [script],
        package_dir = {'': 'lib'},
        packages = [s.pkgname],
        data_files = [
            (os.path.join('share', package, 'examples'), glob.glob(os.path.join('examples', '*'))),
        ],
)

