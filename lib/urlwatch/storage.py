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


import os
import stat
import copy
import platform
import collections
from abc import ABCMeta, abstractmethod

import shutil
import yaml
import minidb
import logging

try:
    import msgpack
except ImportError:
    msgpack = None

try:
    import redis
except ImportError:
    redis = None

try:
    import pwd
except ImportError:
    pwd = None

from .util import atomic_rename, edit_file
from .jobs import JobBase, UrlJob, ShellJob
from .filters import FilterBase

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'display': {
        'new': True,
        'error': True,
        'unchanged': False,
        'empty-diff': True,
    },

    'report': {
        'text': {
            'line_length': 75,
            'details': True,
            'footer': True,
            'minimal': False,
        },

        'markdown': {
            'details': True,
            'footer': True,
            'minimal': False,
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
            'method': 'smtp',
            'smtp': {
                'host': 'localhost',
                'user': '',
                'port': 25,
                'starttls': True,
                'auth': True,
            },
            'sendmail': {
                'path': 'sendmail',
            }
        },
        'pushover': {
            'enabled': False,
            'app': '',
            'device': None,
            'sound': 'spacealarm',
            'user': '',
            'priority': 'normal',
        },
        'pushbullet': {
            'enabled': False,
            'api_key': '',
        },
        'telegram': {
            'enabled': False,
            'bot_token': '',
            'chat_id': '',
            'monospace': False,
            'silent': False,
        },
        'slack': {
            'enabled': False,
            'webhook_url': '',
            'max_message_length': 40000,
        },
        'mattermost': {
            'enabled': False,
            'webhook_url': '',
            'max_message_length': 40000,
        },
        'discord': {
            'enabled': False,
            'embed': False,
            'colored': True,
            'subject': '{count} changes: {jobs}',
            'webhook_url': '',
            'max_message_length': 2000,
        },
        'matrix': {
            'enabled': False,
            'homeserver': '',
            'access_token': '',
            'room_id': '',
        },
        'mailgun': {
            'enabled': False,
            'region': 'us',
            'api_key': '',
            'domain': '',
            'from_mail': '',
            'from_name': '',
            'to': '',
            'subject': '{count} changes: {jobs}'
        },
        'ifttt': {
            'enabled': False,
            'key': '',
            'event': '',
        },
        'xmpp': {
            'enabled': False,
            'sender': '',
            'recipient': '',
        },
        'prowl': {
            'enabled': False,
            'api_key': '',
            'priority': 0,
            'application': '',
            'subject': '{count} changes: {jobs}'
        },
        'shell': {
            'enabled': False,
            'command': '',
            'ignore_stdout': True,
            'ignore_stderr': False,
        },
    },

    'job_defaults': {
        'all': {},
        'shell': {},
        'url': {},
        'browser': {}
    }
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
        return pwd.getpwuid(os.getuid()).pw_name


class BaseStorage(metaclass=ABCMeta):
    @abstractmethod
    def load(self, *args):
        ...

    @abstractmethod
    def save(self, *args):
        ...


class BaseFileStorage(BaseStorage, metaclass=ABCMeta):
    def __init__(self, filename):
        self.filename = filename


class BaseTextualFileStorage(BaseFileStorage, metaclass=ABCMeta):
    def __init__(self, filename):
        super().__init__(filename)
        self.config = {}
        self.load()

    @classmethod
    @abstractmethod
    def parse(cls, *args):
        ...

    def edit(self, example_file=None):
        fn_base, fn_ext = os.path.splitext(self.filename)
        file_edit = fn_base + '.edit' + fn_ext

        if os.path.exists(self.filename):
            shutil.copy(self.filename, file_edit)
        elif example_file is not None and os.path.exists(example_file):
            os.makedirs(os.path.dirname(file_edit) or '.', exist_ok=True)
            shutil.copy(example_file, file_edit)

        while True:
            try:
                edit_file(file_edit)
                # Check if we can still parse it
                if self.parse is not None:
                    self.parse(file_edit)
                break  # stop if no exception on parser
            except SystemExit:
                raise
            except Exception as e:
                print('Parsing failed:')
                print('======')
                print(e)
                print('======')
                print('')
                print('The file', file_edit, 'was NOT updated.')
                user_input = input("Do you want to retry the same edit? (y/n)")
                if user_input.lower()[0] == 'y':
                    continue
                print('Your changes have been saved in', file_edit)
                return 1

        atomic_rename(file_edit, self.filename)
        print('Saving edit changes in', self.filename)
        return 0

    @classmethod
    def write_default_config(cls, filename):
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        config_storage = cls(None)
        config_storage.filename = filename
        config_storage.save()


class UrlsBaseFileStorage(BaseTextualFileStorage, metaclass=ABCMeta):
    def __init__(self, filename):
        self.filename = filename

    def shelljob_security_checks(self):

        if platform.system() == 'Windows':
            return []

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

        def is_shell_job(job):
            if isinstance(job, ShellJob):
                return True

            for filter_kind, subfilter in FilterBase.normalize_filter_list(job.filter):
                if filter_kind == 'shellpipe':
                    return True

                if job.diff_tool is not None:
                    return True

            return False

        # Security checks for shell jobs - only execute if the current UID
        # is the same as the file/directory owner and only owner can write
        shelljob_errors = self.shelljob_security_checks()
        if shelljob_errors and any(is_shell_job(job) for job in jobs):
            print(('Removing shell jobs, because %s' % (' and '.join(shelljob_errors),)))
            jobs = [job for job in jobs if not is_shell_job(job)]

        return jobs


class BaseTxtFileStorage(BaseTextualFileStorage, metaclass=ABCMeta):
    @classmethod
    def parse(cls, *args):
        filename = args[0]
        if filename is not None and os.path.exists(filename):
            with open(filename) as fp:
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


class BaseYamlFileStorage(BaseTextualFileStorage, metaclass=ABCMeta):
    @classmethod
    def parse(cls, *args):
        filename = args[0]
        if filename is not None and os.path.exists(filename):
            with open(filename) as fp:
                return yaml.load(fp, Loader=yaml.SafeLoader)


class YamlConfigStorage(BaseYamlFileStorage):
    def load(self, *args):
        self.config = merge(self.parse(self.filename) or {}, copy.deepcopy(DEFAULT_CONFIG))

    def save(self, *args):
        with open(self.filename, 'w') as fp:
            yaml.dump(self.config, fp, default_flow_style=False)


class UrlsYaml(BaseYamlFileStorage, UrlsBaseFileStorage):
    @classmethod
    def _parse(cls, fp):
        jobs = [JobBase.unserialize(job) for job in yaml.load_all(fp, Loader=yaml.SafeLoader)
                if job is not None]
        jobs_by_guid = collections.defaultdict(list)
        for job in jobs:
            jobs_by_guid[job.get_guid()].append(job)

        conflicting_jobs = []
        for guid, guid_jobs in jobs_by_guid.items():
            if len(guid_jobs) != 1:
                conflicting_jobs.append(guid_jobs[0].get_location())

        if conflicting_jobs:
            raise ValueError('\n   '.join(['Each job must have a unique URL, append #1, #2, ... to make them unique:']
                                          + conflicting_jobs))

        return jobs

    @classmethod
    def parse(cls, *args):
        filename = args[0]
        if filename is not None and os.path.exists(filename):
            with open(filename) as fp:
                return cls._parse(fp)

    def save(self, *args):
        jobs = args[0]
        print('Saving updated list to %r' % self.filename)

        with open(self.filename, 'w') as fp:
            yaml.dump_all([job.serialize() for job in jobs], fp, default_flow_style=False)

    def load(self, *args):
        with open(self.filename) as fp:
            return self._parse(fp)


class UrlsTxt(BaseTxtFileStorage, UrlsBaseFileStorage):
    def load(self):
        return list(self.parse(self.filename))

    def save(self, jobs):
        print(jobs)
        raise NotImplementedError()


class CacheStorage(BaseFileStorage, metaclass=ABCMeta):
    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def get_guids(self):
        ...

    @abstractmethod
    def load(self, job, guid):
        ...

    @abstractmethod
    def save(self, job, guid, data, timestamp, tries, etag=None):
        ...

    @abstractmethod
    def delete(self, guid):
        ...

    @abstractmethod
    def clean(self, guid):
        ...

    def backup(self):
        for guid in self.get_guids():
            data, timestamp, tries, etag = self.load(None, guid)
            yield guid, data, timestamp, tries, etag

    def restore(self, entries):
        for guid, data, timestamp, tries, etag in entries:
            self.save(None, guid, data, timestamp, tries, etag)

    def gc(self, known_guids):
        for guid in set(self.get_guids()) - set(known_guids):
            print('Removing: {guid}'.format(guid=guid))
            self.delete(guid)

        for guid in known_guids:
            count = self.clean(guid)
            if count > 0:
                print('Removed {count} old versions of {guid}'.format(count=count, guid=guid))


class CacheDirStorage(CacheStorage):
    def __init__(self, filename):
        super().__init__(filename)
        if not os.path.exists(filename):
            os.makedirs(filename)

    def close(self):
        #  No need to close
        return 0

    def _get_filename(self, guid):
        return os.path.join(self.filename, guid)

    def get_guids(self):
        return os.listdir(self.filename)

    def load(self, job, guid):
        filename = self._get_filename(guid)
        if not os.path.exists(filename):
            return None, None, None, None

        try:
            with open(filename) as fp:
                data = fp.read()
        except UnicodeDecodeError:
            with open(filename, 'rb') as fp:
                data = fp.read().decode('utf-8', 'ignore')

        timestamp = os.stat(filename)[stat.ST_MTIME]

        return data, timestamp, None, None

    def save(self, job, guid, data, timestamp, etag=None):
        # Timestamp and ETag are always ignored
        filename = self._get_filename(guid)
        with open(filename, 'w+') as fp:
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
    tries = int
    etag = str


class CacheMiniDBStorage(CacheStorage):
    def __init__(self, filename):
        super().__init__(filename)

        dirname = os.path.dirname(filename)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.db = minidb.Store(self.filename, debug=True, vacuum_on_close=False)
        self.db.register(CacheEntry)

    def close(self):
        self.db.close()
        self.db = None

    def get_guids(self):
        return (guid for guid, in CacheEntry.query(self.db, minidb.Function('distinct', CacheEntry.c.guid)))

    def load(self, job, guid):
        for data, timestamp, tries, etag in CacheEntry.query(self.db,
                                                             CacheEntry.c.data // CacheEntry.c.timestamp
                                                             // CacheEntry.c.tries // CacheEntry.c.etag,
                                                             order_by=minidb.columns(CacheEntry.c.timestamp.desc,
                                                                                     CacheEntry.c.tries.desc),
                                                             where=CacheEntry.c.guid == guid, limit=1):
            return data, timestamp, tries, etag

        return None, None, 0, None

    def get_history_data(self, guid, count=1):
        history = {}
        if count < 1:
            return history
        for data, timestamp in CacheEntry.query(self.db, CacheEntry.c.data // CacheEntry.c.timestamp,
                                                order_by=minidb.columns(CacheEntry.c.timestamp.desc,
                                                                        CacheEntry.c.tries.desc),
                                                where=(CacheEntry.c.guid == guid)
                                                & ((CacheEntry.c.tries == 0) | (CacheEntry.c.tries == None))):  # noqa:E711
            if data not in history:
                history[data] = timestamp
                if len(history) >= count:
                    break
        return history

    def save(self, job, guid, data, timestamp, tries, etag=None):
        self.db.save(CacheEntry(guid=guid, timestamp=timestamp, data=data, tries=tries, etag=etag))
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
            self.db.vacuum()
            return result

        return 0


class CacheRedisStorage(CacheStorage):
    def __init__(self, filename):
        super().__init__(filename)

        if redis is None or msgpack is None:
            raise ImportError('redis + msgpack are missing')

        self.db = redis.from_url(filename)

    def _make_key(self, guid):
        return 'guid:' + guid

    def close(self):
        self.db.connection_pool.disconnect()
        self.db = None

    def get_guids(self):
        guids = []
        for guid in self.db.keys(b'guid:*'):
            guids.append(str(guid[len('guid:'):]))
        return guids

    def load(self, job, guid):
        key = self._make_key(guid)
        data = self.db.lindex(key, 0)

        if data:
            r = msgpack.unpackb(data)
            return r['data'], r['timestamp'], r['tries'], r['etag']

        return None, None, 0, None

    def get_history_data(self, guid, count=1):
        history = {}
        if count < 1:
            return history

        key = self._make_key(guid)
        for i in range(0, self.db.llen(key)):
            r = self.db.lindex(key, i)
            c = msgpack.unpackb(r)
            if (c['tries'] == 0 or c['tries'] is None):
                if c['data'] not in history:
                    history[c['data']] = c['timestamp']
                    if len(history) >= count:
                        break
        return history

    def save(self, job, guid, data, timestamp, tries, etag=None):
        r = {
            'data': data,
            'timestamp': timestamp,
            'tries': tries,
            'etag': etag,
        }
        self.db.lpush(self._make_key(guid), msgpack.packb(r, use_bin_type=True))

    def delete(self, guid):
        self.db.delete(self._make_key(guid))

    def clean(self, guid):
        key = self._make_key(guid)
        i = self.db.llen(key)
        if self.db.ltrim(key, 0, 0):
            return i - self.db.llen(key)

        return 0
