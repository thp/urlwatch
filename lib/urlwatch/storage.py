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


import os
import stat
import copy
import platform
from abc import ABCMeta, abstractmethod

import shutil
import yaml
import minidb
import logging

from .util import atomic_rename, edit_file, namedtuple_with_defaults
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
                'keyring': True,
            },
            'sendmail': {
                'path': 'sendmail',
            }
        },
        'pushover': {
            'enabled': False,
            'app': '',
            'device': '',
            'sound': 'spacealarm',
            'user': '',
        },
        'pushbullet': {
            'enabled': False,
            'api_key': '',
        },
        'telegram': {
            'enabled': False,
            'bot_token': '',
            'chat_id': '',
        },
        'slack': {
            'enabled': False,
            'webhook_url': '',
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
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name


def disabled_method(reason=None):
    def method(*args, **kwargs):
        if reason is None:
            raise RuntimeError
        else:
            raise RuntimeError(reason)
    return method


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

        # Security checks for shell jobs - only execute if the current UID
        # is the same as the file/directory owner and only owner can write
        shelljob_errors = self.shelljob_security_checks()
        if shelljob_errors and any(isinstance(job, ShellJob) for job in jobs):
            print(('Removing shell jobs, because %s' % (' and '.join(shelljob_errors),)))
            jobs = [job for job in jobs if not isinstance(job, ShellJob)]

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
    def parse(cls, *args):
        filename = args[0]
        if filename is not None and os.path.exists(filename):
            with open(filename) as fp:
                return [JobBase.unserialize(job) for job in yaml.load_all(fp, Loader=yaml.SafeLoader) if job is not None]

    def save(self, *args):
        jobs = args[0]
        print('Saving updated list to %r' % self.filename)

        with open(self.filename, 'w') as fp:
            yaml.dump_all([job.serialize() for job in jobs], fp, default_flow_style=False)

    def load(self, *args):
        with open(self.filename) as fp:
            return [JobBase.unserialize(job) for job in yaml.load_all(fp, Loader=yaml.SafeLoader) if job is not None]


class UrlsTxt(BaseTxtFileStorage, UrlsBaseFileStorage):
    def load(self):
        return list(self.parse(self.filename))

    def save(self, jobs):
        print(jobs)
        raise NotImplementedError()


class CacheStorage(BaseFileStorage, metaclass=ABCMeta):
    _snapshot = staticmethod(namedtuple_with_defaults(
        '_Snapshot', ['data', 'timestamp'], defaults=(None, None)))

    _loadedcache = staticmethod(namedtuple_with_defaults(
        '_LoadedCache', ['name', 'location', 'last_checked', 'tries', 'etag', 'snapshots'],
        defaults=(None, None, None, 0, None, [])))

    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def get_guids(self):
        ...

    @abstractmethod
    def load(self, guid, count=1):
        """Load last run job state and the most recent `count` distinct snapshots

        Return a namedtuple (
            name, location, last_checked, tries, etag,
            snapshots = [(data, timestamp), ...]
        ), where `snapshots` is a list of namedtuples in reverse chronological order.
        If `count < 0`, all snapshots are loaded.
        """
        ...

    @abstractmethod
    def save(self, guid, data, timestamp):
        """Save a new snapshot"""
        ...

    @abstractmethod
    def update(self, guid, **kwargs):
        """Update last run job state

        Supported keyword arguments:
            name, location, last_checked, last_id, tries, etag
        """
        ...

    @abstractmethod
    def delete(self, guid):
        ...

    @abstractmethod
    def clean(self, guid):
        ...

    def backup(self):
        for guid in self.get_guids():
            loaded_data = self.load(guid, -1)
            yield (guid,) + loaded_data

    def restore(self, entries):
        for guid, name, location, last_checked, tries, etag, snapshots in entries:
            for data, timestamp in reversed(snapshots):
                self.save(guid, data, timestamp)
            self.update(guid, name=name, location=location, last_checked=last_checked, tries=tries, etag=etag)

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
        ...

    def _get_filename(self, guid):
        return os.path.join(self.filename, guid)

    def get_guids(self):
        return os.listdir(self.filename)

    def load(self, guid, count=1):
        filename = self._get_filename(guid)
        if not os.path.exists(filename):
            return self._loadedcache()

        try:
            with open(filename) as fp:
                data = fp.read()
        except UnicodeDecodeError:
            with open(filename, 'rb') as fp:
                data = fp.read().decode('utf-8', 'ignore')
        timestamp = os.stat(filename)[stat.ST_MTIME]
        return self._loadedcache(last_checked=timestamp, snapshots=[self._snapshot(data, timestamp)])

    save = disabled_method('Cannot write to deprecated cache.')
    update = disabled_method('Cannot write to deprecated cache.')
    delete = disabled_method('Cannot write to deprecated cache.')
    clean = disabled_method('Cannot write to deprecated cache.')
    restore = disabled_method('Cannot write to deprecated cache.')
    gc = disabled_method('Cannot write to deprecated cache.')


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

        self.db = minidb.Store(self.filename, debug=True)
        self.db.register(CacheEntry)

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def get_guids(self):
        return (guid for guid, in CacheEntry.query(self.db, minidb.Function('distinct', CacheEntry.c.guid)))

    def load(self, guid, count=1):
        last_checked, tries, etag = next(
            CacheEntry.query(
                self.db,
                CacheEntry.c.timestamp // CacheEntry.c.tries // CacheEntry.c.etag,
                order_by=CacheEntry.c.timestamp.desc,
                where=CacheEntry.c.guid == guid,
                limit=1
            ), (None, 0, None)
        )
        snapshots = []
        for data, timestamp in CacheEntry.query(
                self.db,
                CacheEntry.c.data // CacheEntry.c.timestamp,
                order_by=CacheEntry.c.timestamp.desc,
                where=CacheEntry.c.guid == guid):
            if len(snapshots) >= count >= 0:
                break
            snapshot = self._snapshot(data, timestamp)
            if len(snapshots) >= 1 and snapshots[-1].data == data:
                snapshots[-1] = snapshot
            else:
                snapshots.append(snapshot)
        return self._loadedcache(None, None, last_checked, tries, etag, snapshots)

    save = disabled_method('Cannot write to deprecated cache.')
    update = disabled_method('Cannot write to deprecated cache.')
    delete = disabled_method('Cannot write to deprecated cache.')
    clean = disabled_method('Cannot write to deprecated cache.')
    restore = disabled_method('Cannot write to deprecated cache.')
    gc = disabled_method('Cannot write to deprecated cache.')


class Snapshot(minidb.Model):
    guid = str
    timestamp = int
    data = str


class LastRunState(minidb.Model):
    guid = str
    name = str
    location = str
    last_checked = int
    last_id = int
    tries = int
    etag = str


class CacheMiniDBStorage2(CacheStorage):
    def __init__(self, filename):
        super().__init__(filename)

        dirname = os.path.dirname(filename)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.db = minidb.Store(self.filename, debug=True)
        self.db.register(Snapshot)
        self.db.register(LastRunState)

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def get_guids(self):
        return (guid for guid, in LastRunState.query(self.db, minidb.Function('distinct', LastRunState.c.guid)))

    def load(self, guid, count=1):
        if count == 0:
            snapshots = []
        else:
            last_id = next(
                LastRunState.query(
                    self.db, LastRunState.c.last_id, where=LastRunState.c.guid == guid
                ), (None,))[0]
            snapshots = [self._snapshot(*s) for s in Snapshot.query(
                self.db,
                Snapshot.c.data // Snapshot.c.timestamp,
                where=Snapshot.c.id == last_id)]
            count -= len(snapshots)
            snapshots += [self._snapshot(*s) for s in Snapshot.query(
                self.db,
                Snapshot.c.data // Snapshot.c.timestamp,
                order_by=Snapshot.c.timestamp.desc,
                where=((Snapshot.c.guid == guid) & (Snapshot.c.id != last_id)),
                limit=count
            )]
        name, location, last_checked, tries, etag = next(
            LastRunState.query(
                self.db,
                LastRunState.c.name // LastRunState.c.location // LastRunState.c.last_checked
                // LastRunState.c.tries // LastRunState.c.etag,
                where=LastRunState.c.guid == guid
            ), (None, None, None, 0, None)
        )
        return self._loadedcache(name, location, last_checked, tries, etag, snapshots)

    def save(self, guid, data, timestamp):
        last_id = Snapshot(guid=guid, timestamp=timestamp, data=data).save(self.db).id
        self.db.commit()
        self.update(guid, last_id=last_id)

    def update(self, guid, **kwargs):
        entry = LastRunState.get(self.db, guid=guid)
        if entry is None:
            entry = LastRunState(guid=guid, **kwargs)
        else:
            for k, v in kwargs.items():
                setattr(entry, k, v)
        entry.save(self.db)
        self.db.commit()

    def delete(self, guid):
        Snapshot.delete_where(self.db, Snapshot.c.guid == guid)
        LastRunState.delete_where(self.db, LastRunState.c.guid == guid)
        self.db.commit()

    def clean(self, guid):
        keep_id = next(
            LastRunState.query(
                self.db, LastRunState.c.last_id, where=LastRunState.c.guid == guid
            ), (None,))[0]
        if keep_id is None:
            keep_id = next(
                Snapshot.query(
                    self.db, Snapshot.c.id, where=Snapshot.c.guid == guid,
                    order_by=Snapshot.c.timestamp.desc, limit=1
                ), (None,))[0]
        if keep_id is not None:
            result = Snapshot.delete_where(self.db, (Snapshot.c.guid == guid) & (Snapshot.c.id != keep_id))
            self.db.commit()
            return result
        return 0
