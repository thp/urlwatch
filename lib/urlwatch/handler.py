# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2015 Thomas Perl <thp.io/about>
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
import email.utils
import urllib2
import urlparse
import os
import stat
import sys
import re
import zlib

def get_current_user():
    try:
        return os.getlogin()
    except OSError:
        # If there is no controlling terminal, because urlwatch is launched by
        # cron, or by a systemd.service for example, os.getlogin() fails with:
        # OSError: [Errno 25] Inappropriate ioctl for device
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name

class JobBase(object):
    def __init__(self, location, name=None):
        self.location = location
        self.name = name

    def __str__(self):
        return self.location

    def get_guid(self):
        if have_hashlib:
            sha_hash = hashlib.new('sha1')
            location = self.location
            if isinstance(location, unicode):
                location = location.encode('utf-8')
            sha_hash.update(location)
            return sha_hash.hexdigest()
        else:
            return sha.new(self.location).hexdigest()

    def retrieve(self, timestamp=None, filter_func=None, headers=None,
            log=None):
        raise Exception('Not implemented')

class ShellError(Exception):
    """Exception for shell commands with non-zero exit code"""

    def __init__(self, result):
        Exception.__init__(self)
        self.result = result

    def __str__(self):
        return '%s: Exit status %d' % (self.__class__.__name__, self.result)


def use_filter(filter_func, url, input):
    """Apply a filter function to input from an URL"""
    output = filter_func(url, input)

    if output is None:
        # If the filter does not return a value, it is
        # assumed that the input does not need filtering.
        # In this case, we simply return the input.
        return input

    return output


class ShellJob(JobBase):
    def retrieve(self, timestamp=None, filter_func=None, headers=None,
            log=None):
        process = subprocess.Popen(self.location, \
                stdout=subprocess.PIPE, \
                shell=True)
        stdout_data, stderr_data = process.communicate()
        result = process.wait()
        if result != 0:
            raise ShellError(result)

        return use_filter(filter_func, self.location, stdout_data)


class UrlJob(JobBase):
    CHARSET_RE = re.compile('text/(html|plain); charset=([^;]*)')

    def retrieve(self, timestamp=None, filter_func=None, headers=None,
            log=None):
        headers = dict(headers)
        if timestamp is not None:
            timestamp = email.utils.formatdate(timestamp)
            headers['If-Modified-Since'] = timestamp

        if ' ' in self.location:
            self.location, post_data = self.location.split(' ', 1)
            log.info('Sending POST request to %s', self.location)
        else:
            post_data = None

        parts = urlparse.urlparse(self.location)
        if parts.username or parts.password:
            self.location = urlparse.urlunparse((parts.scheme, parts.hostname, parts.path,
                                                 parts.params, parts.query, parts.fragment))
            log.info('Using HTTP basic authentication for %s', self.location)
            auth_token = urllib2.unquote(':'.join((parts.username, parts.password)))
            headers['Authorization'] = 'Basic %s' % (auth_token.encode('base64').strip())

        request = urllib2.Request(self.location, post_data, headers)
        response = urllib2.urlopen(request)
        headers = response.info()
        content = response.read()
        encoding = 'utf-8'

        # Handle HTTP compression
        compression_type = headers.get('Content-Encoding')
        if compression_type == 'gzip':
            content = zlib.decompress(content, zlib.MAX_WBITS|32)
        elif compression_type == 'deflate':
            content = zlib.decompress(content, -zlib.MAX_WBITS)

        # Determine content type via HTTP headers
        content_type = headers.get('Content-type', '')
        content_type_match = self.CHARSET_RE.match(content_type)
        if content_type_match:
            encoding = content_type_match.group(2)

        # Convert from specified encoding to unicode
        if not isinstance(content, unicode):
            try:
                content = content.decode(encoding, 'ignore')
            except LookupError:
                # If this is an invalid encoding, decode as ascii
                # (Debian bug 731931)
                content = content.decode('ascii', 'ignore')

        return use_filter(filter_func, self.location, content)


def shelljob_security_checks(urls_src):
    shelljob_errors = []
    current_uid = os.getuid()

    dirname = os.path.dirname(urls_src) or '.'
    dir_st = os.stat(dirname)
    if (dir_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
        shelljob_errors.append('%s is group/world-writable' % dirname)
    if dir_st.st_uid != current_uid:
        shelljob_errors.append('%s not owned by %s' % (dirname, get_current_user()))

    file_st = os.stat(urls_src)
    if (file_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
        shelljob_errors.append('%s is group/world-writable' % urls_src)
    if file_st.st_uid != current_uid:
        shelljob_errors.append('%s not owned by %s' % (urls_src, get_current_user()))

    return shelljob_errors


def parse_urls_txt(urls_txt):
    jobs = []

    # Security checks for shell jobs - only execute if the current UID
    # is the same as the file/directory owner and only owner can write
    allow_shelljobs = True
    shelljob_errors = shelljob_security_checks(urls_txt)
    if shelljob_errors:
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

def parse_urls_yaml(urls_yaml):
    import yaml
    jobs = []

    # Security checks for shell jobs - only execute if the current UID
    # is the same as the file/directory owner and only owner can write
    allow_shelljobs = True
    shelljob_errors = shelljob_security_checks(urls_yaml)
    if shelljob_errors:
        allow_shelljobs = False

    with open(urls_yaml, 'r') as f:
        yaml_jobs = yaml.load_all(f)
        for job in yaml_jobs:
            # entries with all parameters commented out
            if job is None:
                continue
            # set all supported keys here, so we don't need to care later
            for key in ['name']:
                if not key in job:
                    job[key] = None
            if not "url" in job:
                print >>sys.stderr, '\n  Entry has no url! Stopping!\n'
                sys.exit(1)
            if job['url'].startswith('|'):
                if allow_shelljobs:
                    jobs.append(ShellJob(job['url'][1:], name=job['name']))
                else:
                    print >>sys.stderr, '\n  SECURITY WARNING - Cannot run shell jobs:\n'
                    for error in shelljob_errors:
                        print >>sys.stderr, '    ', error
                    print >>sys.stderr, '\n  Please remove shell jobs or fix these problems.\n'
                    sys.exit(1)
            else:
                jobs.append(UrlJob(job['url'], name=job['name']))

    return jobs

