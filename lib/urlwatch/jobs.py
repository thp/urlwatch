# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2019 Thomas Perl <m@thp.io>
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


import email.utils
import hashlib
import logging
import os
import re
import subprocess
import requests
import textwrap
import urlwatch
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from .util import TrackSubClasses

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ShellError(Exception):
    """Exception for shell commands with non-zero exit code"""

    def __init__(self, result):
        Exception.__init__(self)
        self.result = result

    def __str__(self):
        return '%s: Exit status %d' % (self.__class__.__name__, self.result)


class NotModifiedError(Exception):
    """Exception raised on HTTP 304 responses"""
    ...


class JobBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}

    __required__ = ()
    __optional__ = ()

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
        for sc in TrackSubClasses.sorted_by_kind(cls):
            if sc.__doc__:
                result.append('  * %s - %s' % (sc.__kind__, sc.__doc__))
            else:
                result.append('  * %s' % (sc.__kind__,))

            for msg, value in (('    Required keys: ', sc.__required__), ('    Optional keys: ', sc.__optional__)):
                if value:
                    values = ('\n' + (len(msg) * ' ')).join(textwrap.wrap(', '.join(value), 79 - len(msg)))
                    result.append('%s%s' % (msg, values))
            result.append('')
        return '\n'.join(result)

    def get_location(self):
        raise NotImplementedError()

    def pretty_name(self):
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
                     if all(required in data for required in subclass.__required__) and not any(
                     key not in subclass.__required__ and key not in subclass.__optional__ for key in data)]

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

    def _set_defaults(self, defaults):
        if isinstance(defaults, dict):
            for key, value in defaults.items():
                if key in self.__optional__ and getattr(self, key) is None:
                    setattr(self, key, value)

    def with_defaults(self, config):
        new_job = JobBase.unserialize(self.serialize())
        cfg = config.get('job_defaults')
        if isinstance(cfg, dict):
            new_job._set_defaults(cfg.get(self.__kind__))
            new_job._set_defaults(cfg.get('all'))
        return new_job

    def get_guid(self):
        location = self.get_location()
        sha_hash = hashlib.new('sha1')
        sha_hash.update(location.encode('utf-8'))
        return sha_hash.hexdigest()

    def retrieve(self, job_state):
        raise NotImplementedError()

    def format_error(self, exception, tb):
        return tb

    def ignore_error(self, exception):
        return False


class Job(JobBase):
    __required__ = ()
    __optional__ = ('name', 'filter', 'max_tries', 'diff_tool', 'compared_versions')

    # determine if hyperlink "a" tag is used in HtmlReporter
    LOCATION_IS_URL = False

    def pretty_name(self):
        return self.name if self.name else self.get_location()


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

        return stdout_data.decode('utf-8')


class UrlJob(Job):
    """Retrieve an URL from a web server"""

    __kind__ = 'url'

    __required__ = ('url',)
    __optional__ = ('cookies', 'data', 'method', 'ssl_no_verify', 'ignore_cached', 'http_proxy', 'https_proxy',
                    'headers', 'ignore_connection_errors', 'ignore_http_error_codes', 'encoding', 'timeout')

    LOCATION_IS_URL = True
    CHARSET_RE = re.compile('text/(html|plain); charset=([^;]*)')

    def get_location(self):
        return self.url

    def retrieve(self, job_state):
        headers = {
            'User-agent': urlwatch.__user_agent__,
        }

        proxies = {
            'http': os.getenv('HTTP_PROXY'),
            'https': os.getenv('HTTPS_PROXY'),
        }

        if job_state.etag is not None:
            headers['If-None-Match'] = job_state.etag

        if job_state.timestamp is not None:
            headers['If-Modified-Since'] = email.utils.formatdate(job_state.timestamp)

        if self.ignore_cached or job_state.tries > 0:
            headers['If-None-Match'] = None
            headers['If-Modified-Since'] = email.utils.formatdate(0)
            headers['Cache-Control'] = 'max-age=172800'
            headers['Expires'] = email.utils.formatdate()

        if self.method is None:
            self.method = "GET"
        if self.data is not None:
            self.method = "POST"
            headers['Content-type'] = 'application/x-www-form-urlencoded'
            logger.info('Sending POST request to %s', self.url)

        if self.http_proxy is not None:
            proxies['http'] = self.http_proxy
        if self.https_proxy is not None:
            proxies['https'] = self.https_proxy

        file_scheme = 'file://'
        if self.url.startswith(file_scheme):
            logger.info('Using local filesystem (%s URI scheme)', file_scheme)
            return open(self.url[len(file_scheme):], 'rt').read()

        if self.headers:
            self.add_custom_headers(headers)

        if self.timeout is None:
            # default timeout
            timeout = 60
        elif self.timeout == 0:
            # never timeout
            timeout = None
        else:
            timeout = self.timeout

        response = requests.request(url=self.url,
                                    data=self.data,
                                    headers=headers,
                                    method=self.method,
                                    verify=(not self.ssl_no_verify),
                                    cookies=self.cookies,
                                    proxies=proxies,
                                    timeout=timeout)

        response.raise_for_status()
        if response.status_code == requests.codes.not_modified:
            raise NotModifiedError()

        # Save ETag from response into job_state, which will be saved in cache
        job_state.etag = response.headers.get('ETag')

        # If we can't find the encoding in the headers, requests gets all
        # old-RFC-y and assumes ISO-8859-1 instead of UTF-8. Use the old
        # urlwatch behavior and try UTF-8 decoding first.
        content_type = response.headers.get('Content-type', '')
        content_type_match = self.CHARSET_RE.match(content_type)
        if not content_type_match and not self.encoding:
            try:
                try:
                    try:
                        return response.content.decode('utf-8')
                    except UnicodeDecodeError:
                        return response.content.decode('latin1')
                except UnicodeDecodeError:
                    return response.content.decode('utf-8', 'ignore')
            except LookupError:
                # If this is an invalid encoding, decode as ascii (Debian bug 731931)
                return response.content.decode('ascii', 'ignore')
        if self.encoding:
            response.encoding = self.encoding

        return response.text

    def add_custom_headers(self, headers):
        """
        Adds custom request headers from the job list (URLs) to the pre-filled dictionary `headers`.
        Pre-filled values of conflicting header keys (case-insensitive) are overwritten by custom value.
        """
        headers_to_remove = [x for x in headers if x.lower() in [y.lower() for y in self.headers]]
        for header in headers_to_remove:
            headers.pop(header, None)
        headers.update(self.headers)

    def format_error(self, exception, tb):
        if isinstance(exception, requests.exceptions.RequestException):
            # Instead of a full traceback, just show the HTTP error
            return str(exception)
        return tb

    def ignore_error(self, exception):
        if isinstance(exception, requests.exceptions.ConnectionError) and self.ignore_connection_errors:
            return True
        elif isinstance(exception, requests.exceptions.HTTPError):
            status_code = exception.response.status_code
            ignored_codes = []
            if isinstance(self.ignore_http_error_codes, int) and self.ignore_http_error_codes == status_code:
                return True
            elif isinstance(self.ignore_http_error_codes, str):
                ignored_codes = [s.strip().lower() for s in self.ignore_http_error_codes.split(',')]
            elif isinstance(self.ignore_http_error_codes, list):
                ignored_codes = [str(s).strip().lower() for s in self.ignore_http_error_codes]
            return str(status_code) in ignored_codes or '%sxx' % (status_code // 100) in ignored_codes
        return False


class BrowserJob(Job):
    """Retrieve an URL, emulating a real web browser"""

    __kind__ = 'browser'

    __required__ = ('navigate',)

    LOCATION_IS_URL = True

    def get_location(self):
        return self.navigate

    def retrieve(self, job_state):
        from requests_html import HTMLSession
        session = HTMLSession()
        response = session.get(self.navigate)
        return response.html.html
