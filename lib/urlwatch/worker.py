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


import concurrent.futures
import logging
import difflib

import requests

from .handler import JobState
from .jobs import NotModifiedError

logger = logging.getLogger(__name__)

MAX_WORKERS = 10


def run_parallel(func, items):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    for future in concurrent.futures.as_completed(executor.submit(func, item) for item in items):
        exception = future.exception()
        if exception is not None:
            raise exception
        yield future.result()


def run_jobs(urlwatcher):
    cache_storage = urlwatcher.cache_storage
    jobs = [job.with_defaults(urlwatcher.config_storage.config)
            for job in urlwatcher.jobs]
    report = urlwatcher.report

    logger.debug('Processing %d jobs', len(jobs))
    for job_state in run_parallel(lambda job_state: job_state.process(),
                                  (JobState(cache_storage, job) for job in jobs)):
        logger.debug('Job finished: %s', job_state.job)

        if not job_state.job.max_tries:
            max_tries = 0
        else:
            max_tries = job_state.job.max_tries
        logger.debug('Using max_tries of %i for %s', max_tries, job_state.job)

        if job_state.exception is not None:
            if job_state.error_ignored:
                logger.info('Error while executing job %s ignored due to job config', job_state.job)
            elif isinstance(job_state.exception, NotModifiedError):
                logger.info('Job %s has not changed (HTTP 304)', job_state.job)
                report.unchanged(job_state)
                if job_state.tries > 0:
                    job_state.tries = 0
                    job_state.save()
            elif job_state.tries < max_tries:
                logger.debug('This was try %i of %i for job %s', job_state.tries,
                             max_tries, job_state.job)
                job_state.save()
            elif job_state.tries >= max_tries:
                logger.debug('We are now at %i tries ', job_state.tries)
                job_state.save()
                report.error(job_state)

        elif job_state.old_data is not None:
            matched_history_time = job_state.history_data.get(job_state.new_data)
            if matched_history_time:
                job_state.timestamp = matched_history_time
            if matched_history_time or job_state.new_data == job_state.old_data:
                report.unchanged(job_state)
                if job_state.tries > 0:
                    job_state.tries = 0
                    job_state.save()
            else:
                close_matches = difflib.get_close_matches(job_state.new_data, job_state.history_data, n=1)
                if close_matches:
                    job_state.old_data = close_matches[0]
                    job_state.timestamp = job_state.history_data[close_matches[0]]
                report.changed(job_state)
                job_state.tries = 0
                job_state.save()
        else:
            report.new(job_state)
            job_state.tries = 0
            job_state.save()
