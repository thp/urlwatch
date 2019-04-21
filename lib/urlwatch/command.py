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


import imp
import logging
import os
import shutil
import sys
import requests

from .filters import FilterBase
from .handler import JobState
from .jobs import JobBase, UrlJob
from .reporters import ReporterBase
from .util import atomic_rename, edit_file
from .mailer import set_password, have_password

logger = logging.getLogger(__name__)


class UrlwatchCommand:
    def __init__(self, urlwatcher):

        self.urlwatcher = urlwatcher
        self.urlwatch_config = urlwatcher.urlwatch_config

    def edit_hooks(self):
        fn_base, fn_ext = os.path.splitext(self.urlwatch_config.hooks)
        hooks_edit = fn_base + '.edit' + fn_ext
        try:
            if os.path.exists(self.urlwatch_config.hooks):
                shutil.copy(self.urlwatch_config.hooks, hooks_edit)
            elif self.urlwatch_config.hooks_py_example is not None and os.path.exists(
                    self.urlwatch_config.hooks_py_example):
                shutil.copy(self.urlwatch_config.hooks_py_example, hooks_edit)
            edit_file(hooks_edit)
            imp.load_source('hooks', hooks_edit)
            atomic_rename(hooks_edit, self.urlwatch_config.hooks)
            print('Saving edit changes in', self.urlwatch_config.hooks)
        except SystemExit:
            raise
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

    def _find_job(self, query):
        try:
            index = int(query)
            if index <= 0:
                return None
            try:
                return self.urlwatcher.jobs[index - 1]
            except IndexError:
                return None
        except ValueError:
            return next((job for job in self.urlwatcher.jobs if job.get_location() == query), None)

    def test_filter(self):
        job = self._find_job(self.urlwatch_config.test_filter)
        job = job.with_defaults(self.urlwatcher.config_storage.config)
        if job is None:
            print('Not found: %r' % (self.urlwatch_config.test_filter,))
            return 1

        if isinstance(job, UrlJob):
            # Force re-retrieval of job, as we're testing filters
            job.ignore_cached = True

        job_state = JobState(self.urlwatcher.cache_storage, job)
        job_state.process()
        if job_state.exception is not None:
            raise job_state.exception
        print(job_state.new_data)
        # We do not save the job state or job on purpose here, since we are possibly modifying the job
        # (ignore_cached) and we do not want to store the newly-retrieved data yet (filter testing)
        return 0

    def run_job(self):
        job = self._find_job(self.urlwatch_config.run_job)
        job = job.with_defaults(self.urlwatcher.config_storage.config)
        if job is None:
            print('Not found: %r' % (self.urlwatch_config.run_job,))
            return 1
        self.urlwatcher.jobs = [job]
        self.urlwatcher.run_jobs()
        self.urlwatcher.close()

    def modify_urls(self):
        save = True
        if self.urlwatch_config.delete is not None:
            job = self._find_job(self.urlwatch_config.delete)
            if job is not None:
                self.urlwatcher.jobs.remove(job)
                print('Removed %r' % (job,))
            else:
                print('Not found: %r' % (self.urlwatch_config.delete,))
                save = False

        if self.urlwatch_config.add is not None:
            # Allow multiple specifications of filter=, so that multiple filters can be specified on the CLI
            items = [item.split('=', 1) for item in self.urlwatch_config.add.split(',')]
            filters = [v for k, v in items if k == 'filter']
            items = [(k, v) for k, v in items if k != 'filter']
            d = {k: v for k, v in items}
            if filters:
                d['filter'] = ','.join(filters)

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
        if self.urlwatch_config.test_filter:
            sys.exit(self.test_filter())
        if self.urlwatch_config.run_job:
            sys.exit(self.run_job())
        if self.urlwatch_config.list:
            sys.exit(self.list_urls())
        if self.urlwatch_config.add is not None or self.urlwatch_config.delete is not None:
            sys.exit(self.modify_urls())

    def check_edit_config(self):
        if self.urlwatch_config.edit_config:
            sys.exit(self.urlwatcher.config_storage.edit())

    def check_telegram_chats(self):
        if self.urlwatch_config.telegram_chats:
            config = self.urlwatcher.config_storage.config['report'].get('telegram', None)
            if not config:
                print('You need to configure telegram in your config first (see README.md)')
                sys.exit(1)

            bot_token = config.get('bot_token', None)
            if not bot_token:
                print('You need to set up your bot token first (see README.md)')
                sys.exit(1)

            info = requests.get('https://api.telegram.org/bot{}/getMe'.format(bot_token)).json()

            chats = {}
            for chat_info in requests.get('https://api.telegram.org/bot{}/getUpdates'.format(bot_token)).json()['result']:
                chat = chat_info['message']['chat']
                if chat['type'] == 'private':
                    chats[str(chat['id'])] = ' '.join((chat['first_name'], chat['last_name'])) if 'last_name' in chat else chat['first_name']

            if not chats:
                print('No chats found. Say hello to your bot at https://t.me/{}'.format(info['result']['username']))
                sys.exit(1)

            headers = ('Chat ID', 'Name')
            maxchat = max(len(headers[0]), max((len(k) for k, v in chats.items()), default=0))
            maxname = max(len(headers[1]), max((len(v) for k, v in chats.items()), default=0))
            fmt = '%-' + str(maxchat) + 's  %s'
            print(fmt % headers)
            print(fmt % ('-' * maxchat, '-' * maxname))
            for k, v in sorted(chats.items(), key=lambda kv: kv[1]):
                print(fmt % (k, v))
            print('\nChat up your bot here: https://t.me/{}'.format(info['result']['username']))
            sys.exit(0)

    def check_test_slack(self):
        if self.urlwatch_config.test_slack:
            config = self.urlwatcher.config_storage.config['report'].get('slack', None)
            if not config:
                print('You need to configure slack in your config first (see README.md)')
                sys.exit(1)

            webhook_url = config.get('webhook_url', None)
            if not webhook_url:
                print('You need to set up your slack webhook_url first (see README.md)')
                sys.exit(1)

            info = requests.post(webhook_url, json={"text": "Test message from urlwatch, your configuration is working"})
            if info.status_code == requests.codes.ok:
                print('Successfully sent message to Slack')
                sys.exit(0)
            else:
                print('Error while submitting message to Slack:{0}'.format(info.text))
                sys.exit(1)

    def check_smtp_login(self):
        if self.urlwatch_config.smtp_login:
            config = self.urlwatcher.config_storage.config['report']['email']
            smtp_config = config['smtp']

            success = True

            if not config['enabled']:
                print('Please enable e-mail reporting in the config first.')
                success = False

            if config['method'] != 'smtp':
                print('Please set the method to SMTP for the e-mail reporter.')
                success = False

            if not smtp_config['keyring']:
                print('Keyring authentication must be enabled for SMTP.')
                success = False

            smtp_hostname = smtp_config['host']
            if not smtp_hostname:
                print('Please configure the SMTP hostname in the config first.')
                success = False

            smtp_username = smtp_config.get('user', None) or config['from']
            if not smtp_username:
                print('Please configure the SMTP user in the config first.')
                success = False

            if not success:
                sys.exit(1)

            if have_password(smtp_hostname, smtp_username):
                message = 'Password for %s / %s already set, update? [y/N] ' % (smtp_username, smtp_hostname)
                if input(message).lower() != 'y':
                    print('Password unchanged.')
                    sys.exit(0)

            if success:
                set_password(smtp_hostname, smtp_username)
                # TODO: Actually verify that the login to the server works

            sys.exit(0)

    def run(self):
        self.check_edit_config()
        self.check_smtp_login()
        self.check_telegram_chats()
        self.check_test_slack()
        self.handle_actions()
        self.urlwatcher.run_jobs()
        self.urlwatcher.close()
