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


import argparse
import logging
import os

import urlwatch
from .migration import migrate_cache, migrate_urls

logger = logging.getLogger(__name__)


class BaseConfig(object):

    def __init__(self, pkgname, urlwatch_dir, config, urls, cache, hooks, verbose):
        self.pkgname = pkgname
        self.urlwatch_dir = urlwatch_dir
        self.config = config
        self.urls = urls
        self.cache = cache
        self.hooks = hooks
        self.verbose = verbose


class CommandConfig(BaseConfig):

    def __init__(self, args, pkgname, urlwatch_dir, prefix, config, urls, hooks, cache, verbose):
        super().__init__(pkgname, urlwatch_dir, config, urls, cache, hooks, verbose)
        self.migrate_cache = migrate_cache
        self.migrate_urls = migrate_urls

        self.examples_dir = os.path.join(prefix, 'share', self.pkgname, 'examples')
        self.urls_yaml_example = os.path.join(self.examples_dir, 'urls.yaml.example')
        self.hooks_py_example = os.path.join(self.examples_dir, 'hooks.py.example')

        self.parse_args(args)

    def parse_args(self, cmdline_args):
        parser = argparse.ArgumentParser(description=urlwatch.__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('joblist', metavar='JOB', type=str, nargs="*", help='indexes or tags of job(s) to run, depending on --tags. If using indexes, they are as numbered according to the --list command. If none are specified, then all jobs will be run.')
        parser.add_argument('--tags', action='store_true', help='Use tags instead of indexes to select jobs to run')
        parser.add_argument('--version', action='version', version='%(prog)s {}'.format(urlwatch.__version__))
        parser.add_argument('-v', '--verbose', action='store_true', help='show debug output')

        group = parser.add_argument_group('files and directories')
        group.add_argument('--urls', metavar='FILE', help='read job list (URLs) from FILE',
                           default=self.urls)
        group.add_argument('--config', metavar='FILE', help='read configuration from FILE',
                           default=self.config)
        group.add_argument('--hooks', metavar='FILE', help='use FILE as hooks.py module',
                           default=self.hooks)
        group.add_argument('--cache', metavar='FILE', help='use FILE as cache database, alternatively can accept a redis URI',
                           default=self.cache)

        group = parser.add_argument_group('Authentication')
        group.add_argument('--smtp-login', action='store_true', help='Enter password for SMTP (store in keyring)')
        group.add_argument('--xmpp-login', action='store_true', help='Enter password for XMPP (store in keyring)')
        group.add_argument('--telegram-chats', action='store_true', help='List telegram chats the bot is joined to')
        group.add_argument('--test-reporter', metavar='REPORTER', help='Send a test notification')

        group = parser.add_argument_group('job list management')
        group.add_argument('--list', action='store_true', help='list jobs')
        group.add_argument('--add', metavar='JOB', help='add job (key1=value1,key2=value2,...)')
        group.add_argument('--delete', metavar='JOB', help='delete job by location or index')
        group.add_argument('--change-location', metavar=('JOB', 'NEW_LOCATION'), nargs=2, help='change the location of an existing job by location or index')
        group.add_argument('--test-filter', metavar='JOB', help='test filter output of job by location or index')
        group.add_argument('--test-diff-filter', metavar='JOB',
                           help='test diff filter output of job by location or index (needs at least 2 snapshots)')
        group.add_argument('--dump-history', metavar='JOB', help='dump historical cached data for a job')

        group = parser.add_argument_group('interactive commands ($EDITOR/$VISUAL)')
        group.add_argument('--edit', action='store_true', help='edit URL/job list')
        group.add_argument('--edit-config', action='store_true', help='edit configuration file')
        group.add_argument('--edit-hooks', action='store_true', help='edit hooks script')

        group = parser.add_argument_group('miscellaneous')
        group.add_argument('--features', action='store_true', help='list supported jobs/filters/reporters')
        group.add_argument('--gc-cache', metavar='RETAIN_LIMIT', type=int, help='remove old cache entries, keeping the latest RETAIN_LIMIT (default: 1)',
                           nargs='?', const=1)

        args = parser.parse_args(cmdline_args)

        if args.tags:
            self.tag_set = frozenset(args.joblist)
        else:
            try:
                self.idx_set = frozenset(int(s) for s in args.joblist)
            except ValueError as e:
                parser.error(e)

        for arg in vars(args):
            argval = getattr(args, arg)
            setattr(self, arg, argval)
