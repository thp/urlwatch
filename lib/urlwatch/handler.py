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

# Python 2 and 3 compatible string check
try:
    str
except NameError:
    str = str

import subprocess
import email.utils
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import urllib.parse
import os
import stat
import sys
import re
import zlib
import yaml
import base64

def get_current_user():
    try:
        return os.getlogin()
    except OSError:
        # If there is no controlling terminal, because urlwatch is launched by
        # cron, or by a systemd.service for example, os.getlogin() fails with:
        # OSError: [Errno 25] Inappropriate ioctl for device
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name


class ShellError(Exception):
    """Exception for shell commands with non-zero exit code"""

    def __init__(self, result):
        Exception.__init__(self)
        self.result = result

    def __str__(self):
        return '%s: Exit status %d' % (self.__class__.__name__, self.result)


class JobState(object):
    def __init__(self, timestamp=None, filter_func=None, headers=None, log=None):
        self.timestamp = timestamp
        self.filter_func = filter_func
        self.headers = headers
        self.log = log

    def process(self, job):
        location = job.get_location()
        data = job.retrieve(self)
        return (self.filter_func(location, data) or data) if self.filter_func is not None else data


class TrackSubClasses(type):
    """A metaclass that stores subclass name-to-class mappings in the base class"""

    def __init__(cls, name, bases, namespace):
        for base in bases:
            if base == object:
                continue

            for attr in ('__required__', '__optional__'):
                inherited = getattr(base, attr, ())
                new_value = tuple(namespace.get(attr, ())) + tuple(inherited)
                namespace[attr] = new_value
                setattr(cls, attr, new_value)

        if hasattr(cls, '__kind__'):
            for base in bases:
                if base == object:
                    continue

                subclasses = getattr(base, '__subclasses__', None)
                if subclasses is not None:
                    subclasses[cls.__kind__] = cls
                    break

        super(TrackSubClasses, cls).__init__(name, bases, namespace)


class JobBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}

    def __init__(self, **kwargs):
        # Set optional keys to None
        for k in self.__optional__:
            if k not in kwargs:
                setattr(self, k, None)

        # Fail if any required keys are not provided
        for k in self.__required__:
            if k not in kwargs:
                raise ValueError('Required field %s missing: %r' % (k, kwargs))

        for k, v in list(kwargs.items()):
            setattr(self, k, v)

    @classmethod
    def job_documentation(cls):
        result = []
        for sc in list(cls.__subclasses__.values()):
            result.extend((
                '  * %s - %s' % (sc.__kind__, sc.__doc__),
                '    Required keys: %s; optional: %s' % (', '.join(sc.__required__), ', '.join(sc.__optional__)),
                '',
            ))
        return '\n'.join(result)

    def get_location(self):
        raise NotImplementedError()

    def serialize(self):
        d = {'kind': self.__kind__}
        d.update(self.to_dict())
        return d

    @classmethod
    def unserialize(cls, data):
        if 'kind' not in data:
            # Try to auto-detect the kind of job based on the available keys
            kinds = [subclass.__kind__ for subclass in list(cls.__subclasses__.values())
                     if all(required in data for required in subclass.__required__) and
                     not any(key not in subclass.__required__ and key not in subclass.__optional__ for key in data)]

            if len(kinds) == 1:
                kind = kinds[0]
            elif len(kinds) == 0:
                raise ValueError('Kind is not specified, and no job matches: %r' % (data,))
            else:
                raise ValueError('Multiple kinds of jobs match %r: %r' % (data, kinds))
        else:
            kind = data['kind']

        return cls.__subclasses__[kind].from_dict(data)

    def to_dict(self):
        return {k: getattr(self, k) for keys in (self.__required__, self.__optional__) for k in keys
                if getattr(self, k) is not None}

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in list(data.items()) if k in cls.__required__ or k in cls.__optional__})

    def __repr__(self):
        return '<%s %s>' % (self.__kind__, ' '.join('%s=%r' % (k, v) for k, v in list(self.to_dict().items())))

    def get_guid(self):
        location = self.get_location()

        if have_hashlib:
            sha_hash = hashlib.new('sha1')
            if isinstance(location, str):
                location = location.encode('utf-8')
            sha_hash.update(location)
            return sha_hash.hexdigest()
        else:
            return sha.new(location).hexdigest()

    def retrieve(self, job_state):
        raise NotImplementedError()


class Job(JobBase):
    __required__ = ()
    __optional__ = ('name',)


class ShellJob(Job):
    """Run a shell command and get its standard output"""

    __kind__ = 'shell'

    __required__ = ('command',)
    __optional__ = ()

    def get_location(self):
        return self.command

    def retrieve(self, job_state):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=True)
        stdout_data, stderr_data = process.communicate()
        result = process.wait()
        if result != 0:
            raise ShellError(result)

        return stdout_data


class UrlJob(Job):
    """Retrieve an URL from a web server"""

    __kind__ = 'url'

    __required__ = ('url',)
    __optional__ = ('post',)

    CHARSET_RE = re.compile('text/(html|plain); charset=([^;]*)')

    def get_location(self):
        return self.url

    def retrieve(self, job_state):
        headers = dict(job_state.headers) if job_state.headers else {}
        if job_state.timestamp is not None:
            headers['If-Modified-Since'] = email.utils.formatdate(job_state.timestamp)

        postdata = None
        if self.post is not None:
            job_state.log.info('Sending POST request to %s', self.url)
            # data might be dict or urlencoded string
            if isinstance(self.post, dict):
                # convert to urlencoded string
                postdata = urllib.parse.urlencode(self.post)
            elif isinstance(self.post, str):
                postdata = self.post
            else:
                # nuke / ignore other data (no string, no dict)
                job_state.log.warning("Ignoring invalid data parameter for url %s: %r", self.url, self.post)

        parts = urllib.parse.urlparse(self.url)
        if parts.username or parts.password:
            url = urllib.parse.urlunparse((parts.scheme, parts.hostname, parts.path,
                                       parts.params, parts.query, parts.fragment))
            job_state.log.info('Using HTTP basic authentication for %s', url)
            auth_token = urllib.parse.unquote(':'.join((parts.username, parts.password)))
            headers['Authorization'] = 'Basic %s' % (base64.b64encode(auth_token).strip())
        else:
            url = self.url

        request = urllib.request.Request(url, postdata, headers)
        response = urllib.request.urlopen(request)
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
        if not isinstance(content, str):
            try:
                content = content.decode(encoding, 'ignore')
            except LookupError:
                # If this is an invalid encoding, decode as ascii
                # (Debian bug 731931)
                content = content.decode('ascii', 'ignore')

        return content


class UrlsStorage(object):
    def __init__(self, filename):
        self.filename = filename

    def shelljob_security_checks(self):
        shelljob_errors = []
        current_uid = os.getuid()

        dirname = os.path.dirname(self.filename) or '.'
        dir_st = os.stat(dirname)
        if (dir_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
            shelljob_errors.append('%s is group/world-writable' % dirname)
        if dir_st.st_uid != current_uid:
            shelljob_errors.append('%s not owned by %s' % (dirname, get_current_user()))

        file_st = os.stat(self.filename)
        if (file_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
            shelljob_errors.append('%s is group/world-writable' % self.filename)
        if file_st.st_uid != current_uid:
            shelljob_errors.append('%s not owned by %s' % (self.filename, get_current_user()))

        return shelljob_errors

    def load_secure(self):
        jobs = self.load()

        # Security checks for shell jobs - only execute if the current UID
        # is the same as the file/directory owner and only owner can write
        shelljob_errors = self.shelljob_security_checks()
        if shelljob_errors and any(isinstance(job, ShellJob) for job in jobs):
            print(('Removing shell jobs, because %s' % (' and '.join(shelljob_errors),)))
            jobs = [job for job in jobs if not isinstance(job, ShellJob)]

        return jobs

    def save(self, jobs):
        raise NotImplementedError()

    def load(self):
        raise NotImplementedError()


class UrlsYaml(UrlsStorage):
    def save(self, jobs):
        with open(self.filename, 'w') as fp:
            yaml.dump_all([job.serialize() for job in jobs], fp, default_flow_style=False)

    def load(self):
        with open(self.filename) as fp:
            return [JobBase.unserialize(job) for job in yaml.load_all(fp) if job is not None]


class UrlsTxt(UrlsStorage):
    def _parse(self, fp):
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('|'):
                yield ShellJob(command=line[1:])
            else:
                args = line.split(None, 2)
                if len(args) == 1:
                    yield UrlJob(url=args[0])
                elif len(args) == 2:
                    yield UrlJob(url=args[0], post=args[1])
                else:
                    raise ValueError('Unsupported line format: %r' % (line,))

    def load(self):
        return list(self._parse(open(self.filename)))
