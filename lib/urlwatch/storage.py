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


import os
import stat
import copy

import yaml
import minidb
import logging

from .jobs import JobBase, UrlJob, ShellJob

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    'display': {
        'new': True,
        'error': True,
        'unchanged': False,
    },

    'report': {
        'text': {
            'line_length': 75,
            'details': True,
            'footer': True,
        },

        'html': {
            'diff': 'unified',  # "unified" or "table"
        },

        'stdout': {
            'enabled': True,
            'color': True,
        },

        'email': {
            'enabled': False,
            'html': False,
            'to': '',
            'from': '',
            'subject': '{count} changes: {jobs}',
            'smtp': {
                'host': 'localhost',
                'port': 25,
                'starttls': True,
                'keyring': True,
            },
        },
    },
}


def merge(source, destination):
    # http://stackoverflow.com/a/20666342
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


def get_current_user():
    try:
        return os.getlogin()
    except OSError:
        # If there is no controlling terminal, because urlwatch is launched by
        # cron, or by a systemd.service for example, os.getlogin() fails with:
        # OSError: [Errno 25] Inappropriate ioctl for device
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name


class ConfigStorage(object):
    def __init__(self, filename):
        self.filename = filename
        self.config = {}
        self.load()

    @classmethod
    def write_default_config(cls, filename):
        config_storage = cls(None)
        config_storage.filename = filename
        config_storage.save()

    def load(self):
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        if self.filename is not None and os.path.exists(self.filename):
            with open(self.filename) as fp:
                self.config = merge(yaml.load(fp), self.config)

    def save(self):
        with open(self.filename, 'w') as fp:
            yaml.dump(self.config, fp, default_flow_style=False)


class UrlsStorage(object):
    def __init__(self, filename):
        self.filename = filename

    def shelljob_security_checks(self):
        shelljob_errors = []
        current_uid = os.getuid()

        dirname = os.path.dirname(self.filename) or '.'
        dir_st = os.stat(dirname)
        if (dir_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
            shelljob_errors.append('%s is group/world-writable' % dirname)
        if dir_st.st_uid != current_uid:
            shelljob_errors.append('%s not owned by %s' % (dirname, get_current_user()))

        file_st = os.stat(self.filename)
        if (file_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)) != 0:
            shelljob_errors.append('%s is group/world-writable' % self.filename)
        if file_st.st_uid != current_uid:
            shelljob_errors.append('%s not owned by %s' % (self.filename, get_current_user()))

        return shelljob_errors

    def load_secure(self):
        jobs = self.load()

        # Security checks for shell jobs - only execute if the current UID
        # is the same as the file/directory owner and only owner can write
        shelljob_errors = self.shelljob_security_checks()
        if shelljob_errors and any(isinstance(job, ShellJob) for job in jobs):
            print(('Removing shell jobs, because %s' % (' and '.join(shelljob_errors),)))
            jobs = [job for job in jobs if not isinstance(job, ShellJob)]

        return jobs

    def save(self, jobs):
        raise NotImplementedError()

    def load(self):
        raise NotImplementedError()


class UrlsYaml(UrlsStorage):
    def save(self, jobs):
        with open(self.filename, 'w') as fp:
            yaml.dump_all([job.serialize() for job in jobs], fp, default_flow_style=False)

    def load(self):
        with open(self.filename) as fp:
            return [JobBase.unserialize(job) for job in yaml.load_all(fp) if job is not None]


class UrlsTxt(UrlsStorage):
    def _parse(self, fp):
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('|'):
                yield ShellJob(command=line[1:])
            else:
                args = line.split(None, 2)
                if len(args) == 1:
                    yield UrlJob(url=args[0])
                elif len(args) == 2:
                    yield UrlJob(url=args[0], post=args[1])
                else:
                    raise ValueError('Unsupported line format: %r' % (line,))

    def load(self):
        return list(self._parse(open(self.filename)))


class CacheStorage(object):
    def __init__(self, filename):
        self.filename = filename

    def close(self):
        ...

    def get_guids(self):
        raise NotImplementedError()

    def load(self, job, guid):
        raise NotImplementedError()

    def save(self, job, guid, data, timestamp):
        raise NotImplementedError()

    def delete(self, guid):
        raise NotImplementedError()

    def clean(self, guid):
        raise NotImplementedError()

    def backup(self):
        for guid in self.get_guids():
            data, timestamp = self.load(None, guid)
            yield guid, data, timestamp

    def restore(self, entries):
        for guid, data, timestamp in entries:
            self.save(None, guid, data, timestamp)

    def gc(self, known_guids):
        for guid in set(self.get_guids()) - set(known_guids):
            print('Removing: {guid}'.format(guid=guid))
            self.delete(guid)

        for guid in known_guids:
            count = self.clean(guid)
            if count > 0:
                print('Removed {count} old versions of {guid}'.format(count=count, guid=guid))


class CacheDirStorage(CacheStorage):
    def _get_filename(self, guid):
        return os.path.join(self.filename, guid)

    def get_guids(self):
        return os.listdir(self.filename)

    def load(self, job, guid):
        filename = self._get_filename(guid)
        if not os.path.exists(filename):
            return None, None

        try:
            with open(filename) as fp:
                data = fp.read()
        except UnicodeDecodeError:
            with open(filename, 'rb') as fp:
                data = fp.read().decode('utf-8', 'ignore')

        timestamp = os.stat(filename)[stat.ST_MTIME]

        return data, timestamp

    def save(self, job, guid, data, timestamp):
        # Timestamp is always ignored
        filename = self._get_filename(guid)
        with open(filename, 'w') as fp:
            fp.write(data)

    def delete(self, guid):
        filename = self._get_filename(guid)
        if os.path.exists(filename):
            os.unlink(filename)

    def clean(self, guid):
        # We only store the latest version, no need to clean
        return 0


class CacheEntry(minidb.Model):
    guid = str
    timestamp = int
    data = str


class CacheMiniDBStorage(CacheStorage):
    def __init__(self, filename):
        super().__init__(filename)
        self.db = minidb.Store(self.filename, debug=True)
        self.db.register(CacheEntry)

    def close(self):
        self.db.close()
        self.db = None

    def get_guids(self):
        return (guid for guid, in CacheEntry.query(self.db, minidb.Function('distinct', CacheEntry.c.guid)))

    def load(self, job, guid):
        for data, timestamp in CacheEntry.query(self.db, CacheEntry.c.data // CacheEntry.c.timestamp,
                                                order_by=CacheEntry.c.timestamp.desc,
                                                where=CacheEntry.c.guid == guid, limit=1):
            return data, timestamp

        return None, None

    def save(self, job, guid, data, timestamp):
        self.db.save(CacheEntry(guid=guid, timestamp=timestamp, data=data))
        self.db.commit()

    def delete(self, guid):
        CacheEntry.delete_where(self.db, CacheEntry.c.guid == guid)
        self.db.commit()

    def clean(self, guid):
        keep_id = next((CacheEntry.query(self.db, CacheEntry.c.id, where=CacheEntry.c.guid == guid,
                                         order_by=CacheEntry.c.timestamp.desc, limit=1)), (None,))[0]

        if keep_id is not None:
            result = CacheEntry.delete_where(self.db, (CacheEntry.c.guid == guid) & (CacheEntry.c.id != keep_id))
            self.db.commit()
            return result

        return 0
