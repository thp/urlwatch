#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# urlwatch is a minimalistic URL watcher written in Python
#
# Copyright (c) 2008-2011 Thomas Perl <thp.io/about>
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
#

try:
    # Available in Python 2.5 and above and preferred if available
    import hashlib
    have_hashlib = True
except ImportError:
    # "sha" is deprecated since Python 2.5 (throws a warning in Python 2.6)
    # Thanks to Frank Palvölgyi for reporting the warning in Python 2.6
    import sha
    have_hashlib = False

import subprocess
import email.Utils
import urllib2
import os
import stat
import sys
import re

class JobBase(object):
    def __init__(self, location):
        self.location = location

    def __str__(self):
        return self.location

    def get_guid(self):
        if have_hashlib:
            sha_hash = hashlib.new('sha1')
            sha_hash.update(self.location)
            return sha_hash.hexdigest()
        else:
            return sha.new(self.location).hexdigest()

    def retrieve(self, timestamp=None, filter=None, headers=None, log=None):
        raise Exception('Not implemented')

class ShellError(Exception):
    """Exception for shell commands with non-zero exit code"""

    def __init__(self, result):
        Exception.__init__(self)
        self.result = result

    def __str__(self):
        return '%s: Exit status %d' % (self.__class__.__name__, self.result)


def use_filter(filter, url, input):
    """Apply a filter function to input from an URL"""
    output = filter(url, input)

    if output is None:
        # If the filter does not return a value, it is
        # assumed that the input does not need filtering.
        # In this case, we simply return the input.
        return input

    return output


class ShellJob(JobBase):
    def retrieve(self, timestamp=None, filter=None, headers=None, log=None):
        process = subprocess.Popen(self.location, \
                stdout=subprocess.PIPE, \
                shell=True)
        stdout_data, stderr_data = process.communicate()
        result = process.wait()
        if result != 0:
            raise ShellError(result)

        return use_filter(filter, self.location, stdout_data)


class UrlJob(JobBase):
    CHARSET_RE = re.compile('text/(html|plain); charset=(.*)')

    def retrieve(self, timestamp=None, filter=None, headers=None, log=None):
        headers = dict(headers)
        if timestamp is not None:
            timestamp = email.Utils.formatdate(timestamp)
            headers['If-Modified-Since'] = timestamp

        if ' ' in self.location:
            self.location, post_data = self.location.split(' ', 1)
            log.info('Sending POST request to %s', self.location)
        else:
            post_data = None

        request = urllib2.Request(self.location, post_data, headers)
        response = urllib2.urlopen(request)
        headers = response.info()
        content = response.read()
        encoding = None

        # Determine content type via HTTP headers
        content_type = headers.get('Content-type', '')
        content_type_match = self.CHARSET_RE.match(content_type)
        if content_type_match:
            encoding = content_type_match.group(2)

        if encoding is not None:
            # Convert from specified encoding to utf-8
            content_unicode = content.decode(encoding, 'ignore')
            content = content_unicode.encode('utf-8')

        return use_filter(filter, self.location, content)


def parse_urls_txt(urls_txt):
    jobs = []

    # Security checks for shell jobs - only execute if the current UID
    # is the same as the file/directory owner and only owner can write
    allow_shelljobs = True
    shelljob_errors = []
    current_uid = os.getuid()

    dirname = os.path.dirname(urls_txt)
    dir_st = os.stat(dirname)
    if (dir_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
        shelljob_errors.append('%s is group/world-writable' % dirname)
        allow_shelljobs = False
    if dir_st.st_uid != current_uid:
        shelljob_errors.append('%s not owned by %s' % (dirname, os.getlogin()))
        allow_shelljobs = False

    file_st = os.stat(urls_txt)
    if (file_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
        shelljob_errors.append('%s is group/world-writable' % urls_txt)
        allow_shelljobs = False
    if file_st.st_uid != current_uid:
        shelljob_errors.append('%s not owned by %s' % (urls_txt, os.getlogin()))
        allow_shelljobs = False

    for line in open(urls_txt).read().splitlines():
        if line.strip().startswith('#') or line.strip() == '':
            continue

        if line.startswith('|'):
            if allow_shelljobs:
                jobs.append(ShellJob(line[1:]))
            else:
                print >>sys.stderr, '\n  SECURITY WARNING - Cannot run shell jobs:\n'
                for error in shelljob_errors:
                    print >>sys.stderr, '    ', error
                print >>sys.stderr, '\n  Please remove shell jobs or fix these problems.\n'
                sys.exit(1)
        else:
            jobs.append(UrlJob(line))

    return jobs

