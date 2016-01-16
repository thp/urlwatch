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

import urlwatch

from .util import TrackSubClasses
from .mailer import send


logger = logging.getLogger(__name__)


class ReporterBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}

    def __init__(self, report, config, job_states, duration):
        self.report = report
        self.config = config
        self.job_states = job_states
        self.duration = duration

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


class TextReporter(ReporterBase):
    def submit(self):
        line_length = self.report.config['report']['text']['line_length']

        summary = []
        details = []
        for job_state in self.report.get_filtered_job_states(self.job_states):
            summary_part, details_part = self._format_output(job_state, line_length)
            summary.extend(summary_part)
            details.extend(details_part)

        if summary:
            sep = line_length * '-'
            yield from itertools.chain(
                (sep, 'summary: %d changes' % (len(summary),), ''),
                ('%02d. %s' % (idx+1, line) for idx, line in enumerate(summary)),
                (sep, '', '', ''),
            )

        if details:
            yield from details
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

        timestamp_old = email.utils.formatdate(job_state.timestamp, localtime=1)
        timestamp_new = email.utils.formatdate(time.time(), localtime=1)
        return ''.join(difflib.unified_diff(job_state.old_data.splitlines(1),
                                            job_state.new_data.splitlines(1),
                                            '@', '@', timestamp_old, timestamp_new))

    def _format_output(self, job_state, line_length):
        summary_part = []
        details_part = []

        summary = ': '.join((job_state.verb.upper(), job_state.job.get_location()))
        content = self._format_content(job_state)

        summary_part.append(summary)

        sep = line_length * '*'
        details_part.extend((sep, summary, sep))
        if content is not None:
            details_part.extend((content, sep))
        details_part.extend(('', ''))

        return summary_part, details_part


class StdoutReporter(TextReporter):
    """Print summary on stdout (the console)"""

    __kind__ = 'stdout'

    def submit(self):
        for line in super().submit():
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

        body = '\n'.join(super().submit())

        # TODO mailer.set_password(options.email_smtp, options.email_from)
        send(self.config['smtp']['host'], self.config['from'], self.config['to'],
             self.config['subject'].format(**subject_args), body,
             self.config['smtp']['starttls'], self.config['smtp']['keyring'])
