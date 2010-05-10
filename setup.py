#!/usr/bin/python
# Generic setup.py file (for urlwatch)
#
# Copyright (c) 2008-2010 Thomas Perl <thp@thpinfo.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from distutils.core import setup

import os
import os.path
import glob
import imp

# name of our package
package = 'urlwatch'

# name of the main script
script = 'urlwatch'

# get program info from urlwatch module
s = imp.load_source('s', script)
# remove compiled file created by imp.load_source
os.unlink(script+'c')

# s.__author__ has the format "Author Name <email>"
author = s.__author__[:s.__author__.index('<')-1]
author_email = s.__author__[s.__author__.index('<')+1:s.__author__.rindex('>')]

setup(
        name = s.pkgname,
        description = s.__doc__,
        version = s.__version__,
        author = author,
        author_email = author_email,
        url = s.__homepage__,
        scripts = [script],
        package_dir = {'': 'lib'},
        packages = [s.pkgname],
        data_files = [
            # Example files
            (os.path.join('share', package, 'examples'),
                glob.glob(os.path.join('examples', '*'))),
            # Manual page
            (os.path.join('share', 'man', 'man1'),
                ['urlwatch.1']),
        ],
)

