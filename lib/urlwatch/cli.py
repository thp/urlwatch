#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2022 Thomas Perl <m@thp.io>
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


# File and folder paths
import logging
import os.path
import signal
import sys

from appdirs import AppDirs

pkgname = 'urlwatch'
urlwatch_dir = os.path.expanduser(os.path.join('~', '.' + pkgname))
urlwatch_cache_dir = AppDirs(pkgname).user_cache_dir

if not os.path.exists(urlwatch_dir):
    urlwatch_dir = AppDirs(pkgname).user_config_dir

# Check if we are installed in the system already
(prefix, bindir) = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))

if bindir != 'bin':
    sys.path.insert(0, os.path.join(prefix, bindir, 'lib'))

from urlwatch.command import UrlwatchCommand
from urlwatch.config import CommandConfig
from urlwatch.main import Urlwatch
from urlwatch.storage import YamlConfigStorage, CacheMiniDBStorage, CacheRedisStorage, UrlsYaml

# Ignore SIGPIPE for stdout (see https://github.com/thp/urlwatch/issues/77)
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except AttributeError:
    # Windows does not have signal.SIGPIPE
    ...

logger = logging.getLogger(pkgname)

CONFIG_FILE = 'urlwatch.yaml'
URLS_FILE = 'urls.yaml'
CACHE_FILE = 'cache.db'
HOOKS_FILE = 'hooks.py'


def setup_logger(verbose):
    if verbose:
        root_logger = logging.getLogger('')
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(asctime)s %(module)s %(levelname)s: %(message)s'))
        root_logger.addHandler(console)
        root_logger.setLevel(logging.DEBUG)
        root_logger.info('turning on verbose logging mode')


def main():
    config_file = os.path.join(urlwatch_dir, CONFIG_FILE)
    urls_file = os.path.join(urlwatch_dir, URLS_FILE)
    hooks_file = os.path.join(urlwatch_dir, HOOKS_FILE)
    new_cache_file = os.path.join(urlwatch_cache_dir, CACHE_FILE)
    old_cache_file = os.path.join(urlwatch_dir, CACHE_FILE)
    cache_file = new_cache_file
    if os.path.exists(old_cache_file) and not os.path.exists(new_cache_file):
        cache_file = old_cache_file

    command_config = CommandConfig(sys.argv[1:], pkgname, urlwatch_dir, bindir, prefix,
                                   config_file, urls_file, hooks_file, cache_file, False)
    setup_logger(command_config.verbose)

    # setup storage API
    config_storage = YamlConfigStorage(command_config.config)

    if any(command_config.cache.startswith(prefix) for prefix in ('redis://', 'rediss://')):
        cache_storage = CacheRedisStorage(command_config.cache)
    else:
        cache_storage = CacheMiniDBStorage(command_config.cache)

    urls_storage = UrlsYaml(command_config.urls)

    # setup urlwatcher
    urlwatch = Urlwatch(command_config, config_storage, cache_storage, urls_storage)
    urlwatch_command = UrlwatchCommand(urlwatch)

    # run urlwatcher
    urlwatch_command.run()


if __name__ == '__main__':
    main()
