#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2016 Thomas Perl <thp.io/about>
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


import itertools
import logging
import difflib
import time
import email.utils
import sys
import cgi

import urlwatch

from .util import TrackSubClasses
from .mailer import Mailer
from .mailer import SendmailMailer
from .mailer import SMTPMailer
import subprocess

try:
    import chump
except ImportError:
    chump = None


logger = logging.getLogger(__name__)


class ReporterBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}

    def __init__(self, report, config, job_states, duration):
        self.report = report
        self.config = config
        self.job_states = job_states
        self.duration = duration

    def convert(self, othercls):
        if hasattr(othercls, '__kind__'):
            config = self.report.config['report'][othercls.__kind__]
        else:
            config = {}

        return othercls(self.report, config, self.job_states, self.duration)

    @classmethod
    def reporter_documentation(cls):
        result = []
        for sc in list(cls.__subclasses__.values()):
            result.extend((
                '  * %s - %s' % (sc.__kind__, sc.__doc__),
            ))
        return '\n'.join(result)

    @classmethod
    def submit_all(cls, report, job_states, duration):
        any_enabled = False
        for name, cls in cls.__subclasses__.items():
            cfg = report.config['report'].get(name, {'enabled': False})
            if cfg['enabled']:
                any_enabled = True
                logger.info('Submitting with %s (%r)', name, cls)
                cls(report, cfg, job_states, duration).submit()

        if not any_enabled:
            logger.warn('No reporters enabled.')

    def submit(self):
        raise NotImplementedError()

    def unified_diff(self, job_state):
        timestamp_old = email.utils.formatdate(job_state.timestamp, localtime=1)
        timestamp_new = email.utils.formatdate(time.time(), localtime=1)
        return ''.join(difflib.unified_diff([l + '\n' for l in job_state.old_data.splitlines()],
                                            [l + '\n' for l in job_state.new_data.splitlines()],
                                            '@', '@', timestamp_old, timestamp_new))


class SafeHtml(object):
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s

    def format(self, *args, **kwargs):
        return str(self).format(*(cgi.escape(str(arg)) for arg in args),
                                **{k: cgi.escape(str(v)) for k, v in kwargs.items()})


class HtmlReporter(ReporterBase):
    def submit(self):
        yield from (str(part) for part in self._parts())

    def _parts(self):
        cfg = self.report.config['report']['html']

        yield SafeHtml("""<!DOCTYPE html>
        <html><head>
            <title>urlwatch</title>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            <style type="text/css">
                body { font-family: sans-serif; }
                .diff_add { color: green; background-color: lightgreen; }
                .diff_sub { color: red; background-color: lightred; }
                .diff_chg { color: orange; background-color: lightyellow; }
                .unified_add { color: green; }
                .unified_sub { color: red; }
                .unified_nor { color: #333; }
                table { font-family: monospace; }
                h2 span.verb { color: #888; }
            </style>
        </head><body>
        """)

        for job_state in self.report.get_filtered_job_states(self.job_states):
            job = job_state.job

            if job.__kind__ == 'url':
                title = '<a href="{location}">{pretty_name}</a>'
            elif job.pretty_name() != job.get_location():
                title = '<span title="{location}">{pretty_name}</span>'
            else:
                title = '{location}'
            title = '<h2><span class="verb">{verb}:</span> '+title+'</h2>'

            yield SafeHtml(title).format(
                    verb=job_state.verb,
                    location=job.get_location(),
                    pretty_name=job.pretty_name())

            content = self._format_content(job_state, cfg['diff'])
            if content is not None:
                yield content

            yield SafeHtml('<hr>')

        yield SafeHtml("""
        <address>
        {pkgname} {version}, {copyright}<br>
        Website: {url}<br>
        watched {count} URLs in {duration} seconds
        </address>
        </body>
        </html>
        """).format(pkgname=urlwatch.pkgname, version=urlwatch.__version__, copyright=urlwatch.__copyright__,
                    url=urlwatch.__url__, count=len(self.job_states), duration=self.duration.seconds)

    def _diff_to_html(self, unified_diff):
        for line in unified_diff.splitlines():
            if line.startswith('+'):
                yield SafeHtml('<span class="unified_add">{line}</span>').format(line=line)
            elif line.startswith('-'):
                yield SafeHtml('<span class="unified_sub">{line}</span>').format(line=line)
            else:
                yield SafeHtml('<span class="unified_nor">{line}</span>').format(line=line)

    def _format_content(self, job_state, difftype):
        if job_state.verb == 'error':
            return SafeHtml('<pre style="text-color: red;">{error}</pre>').format(error=job_state.traceback.strip())

        if job_state.verb == 'unchanged':
            return SafeHtml('<pre>{old_data}</pre>').format(old_data=job_state.old_data)

        if job_state.old_data in (None, job_state.new_data):
            return SafeHtml('...')

        if difftype == 'table':
            timestamp_old = email.utils.formatdate(job_state.timestamp, localtime=1)
            timestamp_new = email.utils.formatdate(time.time(), localtime=1)
            html_diff = difflib.HtmlDiff()
            return SafeHtml(html_diff.make_table(job_state.old_data.splitlines(1), job_state.new_data.splitlines(1),
                                                 timestamp_old, timestamp_new, True, 3))
        elif difftype == 'unified':
            return ''.join((
                '<pre>',
                '\n'.join(self._diff_to_html(self.unified_diff(job_state))),
                '</pre>',
            ))
        else:
            raise ValueError('Diff style not supported: %r', cfg['diff'])


class TextReporter(ReporterBase):
    def submit(self):
        cfg = self.report.config['report']['text']
        line_length = cfg['line_length']
        show_details = cfg['details']
        show_footer = cfg['footer']

        summary = []
        details = []
        for job_state in self.report.get_filtered_job_states(self.job_states):
            summary_part, details_part = self._format_output(job_state, line_length)
            summary.extend(summary_part)
            details.extend(details_part)

        if summary:
            sep = line_length * '='
            yield from itertools.chain(
                (sep,),
                ('%02d. %s' % (idx+1, line) for idx, line in enumerate(summary)),
                (sep, ''),
            )

        if show_details:
            yield from details

        if summary and show_footer:
            yield from ('-- ',
                        '%s %s, %s' % (urlwatch.pkgname, urlwatch.__version__, urlwatch.__copyright__),
                        'Website: %s' % (urlwatch.__url__,),
                        'watched %d URLs in %d seconds' % (len(self.job_states), self.duration.seconds))

    def _format_content(self, job_state):
        if job_state.verb == 'error':
            return job_state.traceback.strip()

        if job_state.verb == 'unchanged':
            return job_state.old_data

        if job_state.old_data in (None, job_state.new_data):
            return None

        return self.unified_diff(job_state)

    def _format_output(self, job_state, line_length):
        summary_part = []
        details_part = []

        pretty_name = job_state.job.pretty_name()
        location = job_state.job.get_location()
        if pretty_name != location:
            location = '%s (%s)' % (pretty_name, location)

        pretty_summary = ': '.join((job_state.verb.upper(), pretty_name))
        summary = ': '.join((job_state.verb.upper(), location))
        content = self._format_content(job_state)

        summary_part.append(pretty_summary)

        sep = line_length * '-'
        details_part.extend((sep, summary, sep))
        if content is not None:
            details_part.extend((content, sep))
        details_part.extend(('', ''))

        return summary_part, details_part


class StdoutReporter(TextReporter):
    """Print summary on stdout (the console)"""

    __kind__ = 'stdout'

    def _incolor(self, color_id, s):
        if sys.stdout.isatty() and self.config.get('color', False):
            return '\033[9%dm%s\033[0m' % (color_id, s)
        return s

    def _red(self, s):
        return self._incolor(1, s)

    def _green(self, s):
        return self._incolor(2, s)

    def _yellow(self, s):
        return self._incolor(3, s)

    def _blue(self, s):
        return self._incolor(4, s)

    def submit(self):
        cfg = self.report.config['report']['text']
        line_length = cfg['line_length']

        separators = (line_length * '=', line_length * '-', '-- ')
        body = '\n'.join(super().submit())

        for line in body.splitlines():
            # FIXME: This isn't ideal, but works for now...
            if line in separators:
                print(line)
            elif line.startswith('+'):
                print(self._green(line))
            elif line.startswith('-'):
                print(self._red(line))
            elif any(line.startswith(prefix) for prefix in ('NEW:', 'CHANGED:', 'UNCHANGED:', 'ERROR:')):
                first, second = line.split(' ', 1)
                if line.startswith('ERROR:'):
                    print(first, self._red(second))
                else:
                    print(first, self._blue(second))
            else:
                print(line)


class EMailReporter(TextReporter):
    """Send summary via e-mail / SMTP"""

    __kind__ = 'email'

    def submit(self):
        filtered_job_states = list(self.report.get_filtered_job_states(self.job_states))

        subject_args = {
            'count': len(filtered_job_states),
            'jobs': ', '.join(job_state.job.pretty_name() for job_state in filtered_job_states),
        }
        subject = self.config['subject'].format(**subject_args)

        body_text = '\n'.join(super().submit())

        if not body_text:
            logger.debug('Not sending e-mail (no changes)')
            return
        if self.config['method'] == "smtp":
            mailer = SMTPMailer(self.config['smtp']['host'], self.config['smtp']['port'],
                                self.config['smtp']['starttls'], self.config['smtp']['keyring'])
        elif self.config['method'] == "sendmail":
            mailer = SendmailMailer(self.config['sendmail']['path'])
        else:
            logger.error('Invalid entry for method {method}'.format(method = self.config['method']))

        # TODO set_password(options.email_smtp, options.email_from)

        if self.config['html']:
            body_html = '\n'.join(self.convert(HtmlReporter).submit())

            msg = mailer.msg_html(self.config['from'], self.config['to'], subject, body_text, body_html)
        else:
            msg = mailer.msg_plain(self.config['from'], self.config['to'], subject, body_text)

        mailer.send(msg)


class PushoverReport(TextReporter):
    """Send summary via Pushover"""

    __kind__ = 'pushover'

    def submit(self):

        body_text = '\n'.join(super().submit())

        if not body_text:
            logger.debug('Not sending pushover (no changes)')
            return

        if len(body_text) > 1024:
            body_text = body_text[0:1023]

        try:
            app = chump.Application(self.config['app'])
        except:
            logger.error("Failed to load chump - is it installed ('pip install chump')")
            return

        user = app.get_user(self.config['user'])

        msg = user.create_message(
            title='Website Change Detected',
            message=body_text,
            html=True,
            sound='spacealarm')

        msg.send()
