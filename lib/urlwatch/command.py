# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2020 Thomas Perl <m@thp.io>
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


import logging
import os
import shutil
import sys
import requests
import traceback

from .filters import FilterBase
from .handler import JobState, Report
from .jobs import JobBase, UrlJob
from .reporters import ReporterBase
from .util import atomic_rename, edit_file, import_module_from_source
from .mailer import set_password, have_password
from .xmpp import xmpp_have_password, xmpp_set_password

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
            import_module_from_source('hooks', hooks_edit)
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
                    print('%d: %s ( %s )' % (idx + 1, pretty_name, location))
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

    def _get_job(self, id):
        job = self._find_job(id)
        if job is None:
            print('Not found: {!r}'.format(id))
            raise SystemExit(1)
        return job.with_defaults(self.urlwatcher.config_storage.config)

    def test_filter(self, id):
        job = self._get_job(id)

        if isinstance(job, UrlJob):
            # Force re-retrieval of job, as we're testing filters
            job.ignore_cached = True

        with JobState(self.urlwatcher.cache_storage, job) as job_state:
            job_state.process()
            if job_state.exception is not None:
                raise job_state.exception
            print(job_state.new_data)
        # We do not save the job state or job on purpose here, since we are possibly modifying the job
        # (ignore_cached) and we do not want to store the newly-retrieved data yet (filter testing)
        return 0

    def test_diff_filter(self, id):
        job = self._get_job(id)

        history_data = self.urlwatcher.cache_storage.get_history_data(job.get_guid(), 10)
        history_data = [key for key, value in sorted(history_data.items(), key=lambda kv: kv[1])]

        if len(history_data) < 2:
            print('Not enough historic data available (need at least 2 different snapshots)')
            return 1

        for i in range(len(history_data) - 1):
            with JobState(self.urlwatcher.cache_storage, job) as job_state:
                job_state.old_data = history_data[i]
                job_state.new_data = history_data[i + 1]
                print('=== Filtered diff between state {} and state {} ==='.format(i, i + 1))
                print(job_state.get_diff())

        # We do not save the job state or job on purpose here, since we are possibly modifying the job
        # (ignore_cached) and we do not want to store the newly-retrieved data yet (filter testing)
        return 0

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
            sys.exit(self.test_filter(self.urlwatch_config.test_filter))
        if self.urlwatch_config.test_diff_filter:
            sys.exit(self.test_diff_filter(self.urlwatch_config.test_diff_filter))
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

    def check_test_reporter(self):
        name = self.urlwatch_config.test_reporter
        if name is None:
            return

        if name not in ReporterBase.__subclasses__:
            print('No such reporter: {}'.format(name))
            print('\nSupported reporters:\n{}\n'.format(ReporterBase.reporter_documentation()))
            sys.exit(1)

        cfg = self.urlwatcher.config_storage.config['report'].get(name, {'enabled': False})
        if not cfg.get('enabled', False):
            print('Reporter is not enabled/configured: {}'.format(name))
            print('Use {} --edit-config to configure reporters'.format(sys.argv[0]))
            sys.exit(1)

        report = Report(self.urlwatcher)

        def build_job(name, url, old, new):
            job = JobBase.unserialize({'name': name, 'url': url})

            # Can pass in None as cache_storage, as we are not
            # going to load or save the job state for testing;
            # also no need to use it as context manager, since
            # no processing is called on the job
            job_state = JobState(None, job)

            job_state.old_data = old
            job_state.new_data = new

            return job_state

        def set_error(job_state, message):
            try:
                raise ValueError(message)
            except ValueError as e:
                job_state.exception = e
                job_state.traceback = job_state.job.format_error(e, traceback.format_exc())

            return job_state

        report.new(build_job('Newly Added', 'http://example.com/new', '', ''))
        report.changed(build_job('Something Changed', 'http://example.com/changed', """
        Unchanged Line
        Previous Content
        Another Unchanged Line
        """, """
        Unchanged Line
        Updated Content
        Another Unchanged Line
        """))
        report.unchanged(build_job('Same As Before', 'http://example.com/unchanged',
                                   'Same Old, Same Old\n',
                                   'Same Old, Same Old\n'))
        report.error(set_error(build_job('Error Reporting', 'http://example.com/error', '', ''), 'Oh Noes!'))

        report.finish_one(name)

        sys.exit(0)

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

            if not smtp_config.get('auth', smtp_config.get('keyring', False)):
                print('Authentication must be enabled for SMTP.')
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

            if 'insecure_password' in smtp_config:
                print('The password is already set in the config (key "insecure_password").')
                sys.exit(0)

            if have_password(smtp_hostname, smtp_username):
                message = 'Password for %s / %s already set, update? [y/N] ' % (smtp_username, smtp_hostname)
                if input(message).lower() != 'y':
                    print('Password unchanged.')
                    sys.exit(0)

            if success:
                set_password(smtp_hostname, smtp_username)
                # TODO: Actually verify that the login to the server works

            sys.exit(0)

    def check_xmpp_login(self):
        if self.urlwatch_config.xmpp_login:
            xmpp_config = self.urlwatcher.config_storage.config['report']['xmpp']

            success = True

            if not xmpp_config['enabled']:
                print('Please enable XMPP reporting in the config first.')
                success = False

            xmpp_sender = xmpp_config.get('sender')
            if not xmpp_sender:
                print('Please configure the XMPP sender in the config first.')
                success = False

            if not xmpp_config.get('recipient'):
                print('Please configure the XMPP recipient in the config first.')
                success = False

            if not success:
                sys.exit(1)

            if 'insecure_password' in xmpp_config:
                print('The password is already set in the config (key "insecure_password").')
                sys.exit(0)

            if xmpp_have_password(xmpp_sender):
                message = 'Password for %s already set, update? [y/N] ' % (xmpp_sender)
                if input(message).lower() != 'y':
                    print('Password unchanged.')
                    sys.exit(0)

            if success:
                xmpp_set_password(xmpp_sender)

            sys.exit(0)

    def run(self):
        self.check_edit_config()
        self.check_smtp_login()
        self.check_telegram_chats()
        self.check_xmpp_login()
        self.check_test_reporter()
        self.handle_actions()
        self.urlwatcher.run_jobs()
        self.urlwatcher.close()
