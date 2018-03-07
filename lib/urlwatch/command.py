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


import imp
import logging
import os
import shutil
import subprocess
import sys

from .filters import FilterBase
from .jobs import JobBase
from .reporters import ReporterBase
from .util import atomic_rename

logger = logging.getLogger(__name__)


class UrlwatchCommand:
    def __init__(self, urlwatcher):

        self.urlwatcher = urlwatcher
        self.urlwatch_config = urlwatcher.urlwatch_config

    def edit_hooks(self):

        editor = os.environ.get('EDITOR', None)
        if editor is None:
            editor = os.environ.get('VISUAL', None)
        if editor is None:
            editor = shutil.which('editor', os.X_OK)
        if editor is None:
            print('Please set $VISUAL or $EDITOR.')
            return 1

        fn_base, fn_ext = os.path.splitext(self.urlwatch_config.hooks)
        hooks_edit = fn_base + '.edit' + fn_ext
        try:
            if os.path.exists(self.urlwatch_config.hooks):
                shutil.copy(self.urlwatch_config.hooks, hooks_edit)
            elif self.urlwatch_config.hooks_py_example is not None and os.path.exists(
                    self.urlwatch_config.hooks_py_example):
                shutil.copy(self.urlwatch_config.hooks_py_example, hooks_edit)
            subprocess.check_call([editor, hooks_edit])
            imp.load_source('hooks', hooks_edit)
            atomic_rename(hooks_edit, self.urlwatch_config.hooks)
            print('Saving edit changes in', self.urlwatch_config.hooks)
        except Exception as e:
            print('Parsing failed:')
            print('======')
            print(e)
            print('======')
            print('')
            print('The file', self.urlwatch_config.hooks, 'was NOT updated.')
            print('Your changes have been saved in', hooks_edit)
            return 1

        return 0

    def show_features(self):
        print()
        print('Supported jobs:\n')
        print(JobBase.job_documentation())

        print('Supported filters:\n')
        print(FilterBase.filter_documentation())
        print()
        print('Supported reporters:\n')
        print(ReporterBase.reporter_documentation())
        print()
        return 0

    def list_urls(self):
        for idx, job in enumerate(self.urlwatcher.jobs):
            if self.urlwatch_config.verbose:
                print('%d: %s' % (idx + 1, repr(job)))
            else:
                pretty_name = job.pretty_name()
                location = job.get_location()
                if pretty_name != location:
                    print('%d: %s (%s)' % (idx + 1, pretty_name, location))
                else:
                    print('%d: %s' % (idx + 1, pretty_name))
        return 0

    def modify_urls(self):
        save = True
        if self.urlwatch_config.delete is not None:
            try:
                index = int(self.urlwatch_config.delete) - 1
                try:
                    job = self.urlwatcher.jobs.pop(index)
                    print('Removed %r' % (job,))
                except IndexError:
                    print('Not found: %r' % (index,))
                    save = False
            except ValueError:
                job = next((job for job in self.urlwatcher.jobs if job.get_location() == self.urlwatch_config.delete),
                           None)
                try:
                    self.urlwatcher.jobs.remove(job)
                    print('Removed %r' % (job,))
                except ValueError:
                    print('Not found: %r' % (self.urlwatch_config.delete,))
                    save = False

        if self.urlwatch_config.add is not None:
            d = {k: v for k, v in (item.split('=', 1) for item in self.urlwatch_config.add.split(','))}
            job = JobBase.unserialize(d)
            print('Adding %r' % (job,))
            self.urlwatcher.jobs.append(job)

        if save:
            self.urlwatcher.urls_storage.save(self.urlwatcher.jobs)

        return 0

    def handle_actions(self):
        if self.urlwatch_config.features:
            sys.exit(self.show_features())
        if self.urlwatch_config.gc_cache:
            self.urlwatcher.cache_storage.gc([job.get_guid() for job in self.urlwatcher.jobs])
            sys.exit(0)
        if self.urlwatch_config.edit:
            sys.exit(self.urlwatcher.urls_storage.edit(self.urlwatch_config.urls_yaml_example))
        if self.urlwatch_config.edit_hooks:
            sys.exit(self.edit_hooks())
        if self.urlwatch_config.list:
            sys.exit(self.list_urls())
        if self.urlwatch_config.add is not None or self.urlwatch_config.delete is not None:
            sys.exit(self.modify_urls())

    def check_edit_config(self):
        if self.urlwatch_config.edit_config:
            sys.exit(self.urlwatcher.config_storage.edit())

    def run(self):

        self.check_edit_config()
        self.handle_actions()
        self.urlwatcher.run_jobs()
        self.urlwatcher.close()
