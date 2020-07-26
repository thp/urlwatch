# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2020 Thomas Perl <m@thp.io>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
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


import re
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def html2text(data, baseurl, method, options):
    """
    Convert a string consisting of HTML to plain text
    for easy difference checking.

    Method may be one of:
     'lynx'           - Use "lynx -dump" for conversion
                        options: see "lynx -help" output for options that work with "-dump"
     'html2text'      - Use "html2text -nobs" for conversion
                        options: https://linux.die.net/man/1/html2text
     'bs4'            - Use Beautiful Soup library to prettify the HTML
                        options: "parser" only, bs4 supports "lxml", "html5lib", and "html.parser"
                        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#specifying-the-parser-to-use
     're'             - A simple regex-based HTML tag stripper
     'pyhtml2text'    - Use Python module "html2text"
                        options: https://github.com/Alir3z4/html2text/blob/master/docs/usage.md#available-options
    """
    if method == 're':
        stripped_tags = re.sub(r'<[^>]*>', '', data)
        d = '\n'.join((line.rstrip() for line in stripped_tags.splitlines() if line.strip() != ''))
        return d

    if method == 'pyhtml2text':
        import html2text
        parser = html2text.HTML2Text()
        parser.baseurl = baseurl
        for k, v in options.items():
            setattr(parser, k.lower(), v)
        d = parser.handle(data)
        return d

    if method == 'bs4':
        from bs4 import BeautifulSoup
        parser = options.pop('parser', 'lxml')
        soup = BeautifulSoup(data, parser)
        d = soup.get_text(strip=True)
        return d

    if method == 'lynx':
        cmd = ['lynx', '-nonumbers', '-dump', '-stdin', '-assume_charset UTF-8', '-display_charset UTF-8']
    elif method == 'html2text':
        cmd = ['html2text', '-nobs', '-utf8']
    else:
        raise ValueError('Unknown html2text method: %r' % (method,))

    stdout_encoding = 'utf-8'

    for k, v in options.items():
        if v is not None:
            cmd.append('-{} {}'.format(k, v))
        else:
            cmd.append('-{}'.format(k))

    logger.debug('Command: %r, stdout encoding: %s', cmd, stdout_encoding)

    env = {}
    env.update(os.environ)
    env['LANG'] = 'en_US.utf-8'
    env['LC_ALL'] = 'en_US.utf-8'

    html2text = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
    stdout, stderr = html2text.communicate(data.encode('utf-8'))
    stdout = stdout.decode(stdout_encoding)

    if method == 'lynx':
        # Lynx translates relative links in the mode we use it to:
        # file://localhost/tmp/[RANDOM STRING]/[RELATIVE LINK]

        # Recent versions of lynx (seen in 2.8.8pre1-1) do not include the
        # "localhost" in the file:// URLs; see Debian bug 732112
        stdout = re.sub(r'file://%s/[^/]*/' % (os.environ.get('TMPDIR', '/tmp'),), '', stdout)

        # Use the following regular expression to remove the unnecessary
        # parts, so that [RANDOM STRING] (changing on each call) does not
        # expose itself as change on the website (it's a Lynx-related thing
        # Thanks to Evert Meulie for pointing that out
        stdout = re.sub(r'file://localhost%s/[^/]*/' % (os.environ.get('TMPDIR', '/tmp'),), '', stdout)
        # Also remove file names like L9816-5928TMP.html
        stdout = re.sub(r'L\d+-\d+TMP.html', '', stdout)

    return stdout.strip()
