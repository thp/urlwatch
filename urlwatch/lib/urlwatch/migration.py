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


import os.path
import logging
from urlwatch.storage import UrlsYaml, UrlsTxt, CacheDirStorage, CacheMiniDBStorage

logger = logging.getLogger(__name__)


class MigrationManager(object):

    def __init__(self, config, args):
        self.config = config
        self.args = args

    def migrate_jobs_to_urlwatch_2x(self):
        # Migrate urlwatch 1.x URLs to urlwatch 2.x
        if os.path.isfile(self.config.urls_txt) and not os.path.isfile(self.args.urls):
            print("""
            Migrating URLs: {urls_txt} -> {urls_yaml}
            Use "{pkgname} --edit" to customize it.
            """.format(urls_txt=self.config.urls_txt, urls_yaml=self.args.urls, pkgname=self.config.pkgname))
            UrlsYaml(self.args.urls).save(UrlsTxt(self.config.urls_txt).load_secure())
            os.rename(self.config.urls_txt, self.config.urls_txt + '.migrated')

    def migrate_cache_to_urlwatch_2x(self, jobs):
        # Migrate urlwatch 1.x cache to urlwatch 2.x
        if not os.path.isfile(self.args.cache) and os.path.isdir(self.config.cache_dir):
            print("""
            Migrating cache: {cache_dir} -> {cache_db}
            """.format(cache_dir=self.config.cache_dir, cache_db=self.args.cache))
            cache_storage = CacheMiniDBStorage(self.args.cache)
            old_cache_storage = CacheDirStorage(self.config.cache_dir)
            cache_storage.restore(old_cache_storage.backup())
            cache_storage.gc([job.get_guid() for job in jobs])
            os.rename(self.config.cache_dir, self.config.cache_dir + '.migrated')
        else:
            cache_storage = CacheMiniDBStorage(self.args.cache)
        return cache_storage