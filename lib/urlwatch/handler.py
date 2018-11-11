# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2018 Thomas Perl <m@thp.io>
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


import datetime
import logging
import time
import traceback

from .filters import FilterBase
from .jobs import NotModifiedError
from .reporters import ReporterBase

logger = logging.getLogger(__name__)


class JobState(object):
    def __init__(self, cache_storage, job):
        self.cache_storage = cache_storage
        self.job = job
        self.verb = None
        self.old_data = None
        self.new_data = None
        self.timestamp = None
        self.exception = None
        self.traceback = None
        self.tries = 0
        self.etag = None

    def load(self):
        self.old_data, self.timestamp, self.tries, self.etag = self.cache_storage.load(self.job, self.job.get_guid())
        if self.tries is None:
            self.tries = 0

    def save(self):
        if self.new_data is None and self.exception is not None:
            # If no new data has been retrieved due to an exception, use the old job data
            self.new_data = self.old_data

        self.cache_storage.save(self.job, self.job.get_guid(), self.new_data, time.time(), self.tries, self.etag)

    def process(self):
        logger.info('Processing: %s', self.job)
        try:
            self.load()
            data = self.job.retrieve(self)

            # Apply automatic filters first
            data = FilterBase.auto_process(self, data)

            # Apply any specified filters
            filter_list = self.job.filter

            if filter_list:
                if isinstance(filter_list, list):
                    for item in filter_list:
                        key = next(iter(item))
                        filter_kind, subfilter = key, item[key]
                        data = FilterBase.process(filter_kind, subfilter, self, data)
                elif isinstance(filter_list, str):
                    for filter_kind in filter_list.split(','):
                        if ':' in filter_kind:
                            filter_kind, subfilter = filter_kind.split(':', 1)
                        else:
                            subfilter = None
                        data = FilterBase.process(filter_kind, subfilter, self, data)
            self.new_data = data

        except Exception as e:
            self.exception = e
            self.traceback = traceback.format_exc()
            if not isinstance(e, NotModifiedError):
                self.tries += 1
                logger.debug('Increasing number of tries to %i for %s', self.tries, self.job)

        return self


class Report(object):
    def __init__(self, urlwatch_config):
        self.config = urlwatch_config.config_storage.config

        self.job_states = []
        self.start = datetime.datetime.now()

    def _result(self, verb, job_state):
        if job_state.exception is not None:
            # TODO: Once we require Python >= 3.5, we can just pass in job_state.exception as "exc_info" parameter
            exc_info = (type(job_state.exception), job_state.exception, job_state.exception.__traceback__)
            logger.debug('Got exception while processing %r', job_state.job, exc_info=exc_info)

        job_state.verb = verb
        self.job_states.append(job_state)

    def new(self, job_state):
        self._result('new', job_state)

    def changed(self, job_state):
        self._result('changed', job_state)

    def unchanged(self, job_state):
        self._result('unchanged', job_state)

    def error(self, job_state):
        self._result('error', job_state)

    def get_filtered_job_states(self, job_states):
        for job_state in job_states:
            if not any(job_state.verb == verb and not self.config['display'][verb]
                       for verb in ('unchanged', 'new', 'error')):
                yield job_state

    def finish(self):
        end = datetime.datetime.now()
        duration = (end - self.start)

        ReporterBase.submit_all(self, self.job_states, duration)
