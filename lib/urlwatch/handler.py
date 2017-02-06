# -*- coding: utf-8 -*-
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


import datetime
import logging
import time
import traceback

from .filters import FilterBase
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

    def load(self):
        self.old_data, self.timestamp = self.cache_storage.load(self.job, self.job.get_guid())

    def save(self):
        self.cache_storage.save(self.job, self.job.get_guid(), self.new_data, time.time())

    def process(self):
        logger.info('Processing: %s', self.job)
        try:
            self.load()
            data = self.job.retrieve(self)

            # Apply automatic filters first
            data = FilterBase.auto_process(self, data)

            # Apply any specified filters
            filter_list = self.job.filter
            if filter_list is not None:
                for filter_kind in re.split(',', filter_list):
                    if ':' in filter_kind:
                        filter_kind, subfilter = re.split(':', filter_kind, 1)
                    else:
                        subfilter = None

                    logger.info('Applying filter %r, subfilter %r to %s',
                                filter_kind, subfilter, self.job.get_location())
                    data = FilterBase.process(filter_kind, subfilter, self, data)

            self.new_data = data
        except Exception as e:
            self.exception = e
            self.traceback = traceback.format_exc()

        return self


class Report(object):
    def __init__(self, urlwatch_config):
        self.config = urlwatch_config.config_storage.config

        self.job_states = []
        self.start = datetime.datetime.now()

    def _result(self, verb, job_state):
        if job_state.exception is not None:
            logger.debug('Got exception while processing %r: %s', job_state.job, job_state.exception)

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
