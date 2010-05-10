#!/usr/bin/python
# Convert HTML data to plaintext using Lynx, html2text or a regex
# Requirements: Either lynx (default) or html2text or simply Python (for regex)
# This file is part of urlwatch
#
# Copyright (c) 2009-2010 Thomas Perl <thp@thpinfo.com>
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


import re

def html2text(data, method='lynx'):
    """
    Convert a string consisting of HTML to plain text
    for easy difference checking.

    Method may be one of:
     'lynx' (default) - Use "lynx -dump" for conversion
     'html2text'      - Use "html2text -nobs" for conversion
     're'             - A simple regex-based HTML tag stripper
    
    Dependencies: apt-get install lynx html2text
    """
    if method == 're':
        stripped_tags = re.sub(r'<[^>]*>', '', data)
        d = '\n'.join((l.rstrip() for l in stripped_tags.splitlines() if l.strip() != ''))
        return d

    if method == 'lynx':
        cmd = ['lynx', '-dump', '-stdin']
    elif method == 'html2text':
        cmd = ['html2text', '-nobs']
    else:
        return data

    import subprocess
    html2text = subprocess.Popen(cmd, stdin=subprocess.PIPE, \
            stdout=subprocess.PIPE)
    (stdout, stderr) = html2text.communicate(data)

    if method == 'lynx':
        # Lynx translates relative links in the mode we use it to:
        # file://localhost/tmp/[RANDOM STRING]/[RELATIVE LINK]
        # Use the following regular expression to remove the unnecessary
        # parts, so that [RANDOM STRING] (changing on each call) does not
        # expose itself as change on the website (it's a Lynx-related thing
        # Thanks to Evert Meulie for pointing that out
        stdout = re.sub(r'file://localhost/tmp/[^/]*/', '', stdout)
        # Also remove file names like L9816-5928TMP.html
        stdout = re.sub(r'L\d+-\d+TMP.html', '', stdout)

    return stdout


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        print html2text(open(sys.argv[1]).read())
    else:
        print 'Usage: %s document.html' % (sys.argv[0])
        sys.exit(1)

