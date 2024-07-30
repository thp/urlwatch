# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2023 Thomas Perl <m@thp.io>
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
import datetime

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
                os.makedirs(os.path.dirname(hooks_edit) or '.', exist_ok=True)
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
        for idx, job in enumerate(self.urlwatcher.jobs, 1):
            if self.urlwatch_config.verbose:
                print('%d: %s' % (idx, repr(job)))
            else:
                pretty_name = job.pretty_name()
                location = job.get_location()
                if pretty_name != location:
                    print('%d: %s ( %s )' % (idx, pretty_name, location))
                else:
                    print('%d: %s' % (idx, pretty_name))
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

    def _resolve_job_history(self, id, max_entries=10):
        job = self._get_job(id)

        history_data = self.urlwatcher.cache_storage.get_history_data(job.get_guid(), max_entries)
        history_data = sorted(history_data.items(), key=lambda kv: kv[1])

        return job, history_data

    def test_diff_filter(self, id):
        job, history_data = self._resolve_job_history(id)

        if len(history_data) and getattr(job, 'treat_new_as_changed', False):
            # Insert empty history entry, so first snapshot is diffed against the empty string
            _, first_timestamp = history_data[0]
            history_data.insert(0, ('', first_timestamp))

        if len(history_data) < 2:
            print('Not enough historic data available (need at least 2 different snapshots)')
            return 1

        for i in range(len(history_data) - 1):
            with JobState(self.urlwatcher.cache_storage, job) as job_state:
                job_state.old_data, job_state.timestamp = history_data[i]
                job_state.new_data, job_state.current_timestamp = history_data[i + 1]
                print('=== Filtered diff between state {} and state {} ==='.format(i, i + 1))
                print(job_state.get_diff())

        # We do not save the job state or job on purpose here, since we are possibly modifying the job
        # (ignore_cached) and we do not want to store the newly-retrieved data yet (filter testing)
        return 0

    def dump_history(self, id):
        job, history_data = self._resolve_job_history(id)

        for entry_data, entry_timestamp in history_data:
            print('=' * 30)
            dt = datetime.datetime.fromtimestamp(entry_timestamp)
            print(dt.strftime('%Y-%m-%d %H:%M'))
            print('-' * 30)
            print(entry_data)
            print('=' * 30, '\n')

        print('{} historic snapshot(s) available'.format(len(history_data)))

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

        if self.urlwatch_config.enable is not None:
            job = self._find_job(self.urlwatch_config.enable)
            if job is not None:
                job.enabled = True
                print(f'Enabled {job!r}')
            else:
                print(f'Not found: {self.urlwatch_config.enable!r}')
                save = False

        if self.urlwatch_config.disable is not None:
            job = self._find_job(self.urlwatch_config.disable)
            if job is not None:
                job.enabled = False
                print(f'Disabled {job!r}')
            else:
                print(f'Not found: {self.urlwatch_config.disable!r}')
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

        if self.urlwatch_config.change_location is not None:
            new_loc = self.urlwatch_config.change_location[1]
            # Ensure the user isn't overwriting an existing job with the change.
            if new_loc in (j.get_location() for j in self.urlwatcher.jobs):
                print(f'The new location "{new_loc}" already exists for a job. '
                      'Delete the existing job or choose a different value.')
                save = False
            else:
                job = self._find_job(self.urlwatch_config.change_location[0])
                if job is not None:
                    # Update the job's location (which will also update the
                    # guid) and move any history in the cache over to the job's
                    # updated guid.
                    print(f'Moving location of {job!r} to "{new_loc}"')
                    old_guid = job.get_guid()
                    old_loc = job.get_location()
                    job.set_base_location(new_loc)
                    num_moved = self.urlwatcher.cache_storage.move(
                        old_guid, job.get_guid())
                    if num_moved:
                        print(f'Moved {num_moved} snapshots of "{old_loc}" to "{new_loc}"')
                else:
                    print(f'Not found: {self.urlwatch_config.change_location[0]}')
                    save = False

        if save:
            self.urlwatcher.urls_storage.save(self.urlwatcher.jobs)

        return 0

    def handle_actions(self):
        if self.urlwatch_config.features:
            sys.exit(self.show_features())
        if self.urlwatch_config.gc_cache is not None:
            self.urlwatcher.cache_storage.gc([job.get_guid() for job in self.urlwatcher.jobs], self.urlwatch_config.gc_cache)
            sys.exit(0)
        if self.urlwatch_config.edit:
            sys.exit(self.urlwatcher.urls_storage.edit(self.urlwatch_config.urls_yaml_example))
        if self.urlwatch_config.edit_hooks:
            sys.exit(self.edit_hooks())
        if self.urlwatch_config.test_filter:
            sys.exit(self.test_filter(self.urlwatch_config.test_filter))
        if self.urlwatch_config.test_diff_filter:
            sys.exit(self.test_diff_filter(self.urlwatch_config.test_diff_filter))
        if self.urlwatch_config.dump_history:
            sys.exit(self.dump_history(self.urlwatch_config.dump_history))
        if self.urlwatch_config.list:
            sys.exit(self.list_urls())
        if (self.urlwatch_config.add is not None
                or self.urlwatch_config.delete is not None
                or self.urlwatch_config.enable is not None
                or self.urlwatch_config.disable is not None
                or self.urlwatch_config.change_location is not None):
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
