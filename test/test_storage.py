import sys
import os
import shutil
import time
import tempfile
import binascii
import imp
from urlwatch.jobs import UrlJob, ShellJob
from urlwatch import storage
from urlwatch.storage import UrlsYaml, UrlsTxt
from urlwatch.storage import YamlConfigStorage
from urlwatch.storage import CacheDirStorage, CacheMiniDBStorage, CacheMiniDBStorage2
from urlwatch.migration import migrate_urls, migrate_cache

from util import REPO_ROOT, TEST_DATA_DIR, TestConfig


def test_save_load_jobs():
    jobs = [
        UrlJob(name='news', url='http://news.orf.at/'),
        ShellJob(name='list homedir', command='ls ~'),
        ShellJob(name='list proc', command='ls /proc'),
    ]

    # tempfile.NamedTemporaryFile() doesn't work on Windows
    # because the returned file object cannot be opened again
    with tempfile.TemporaryDirectory() as tempdir:
        name = os.path.join(tempdir, 'urls.yaml')
        UrlsYaml(name).save(jobs)
        jobs2 = UrlsYaml(name).load()
        os.chmod(name, 0o777)
        jobs3 = UrlsYaml(name).load_secure()

    assert len(jobs2) == len(jobs)
    # Assert that the shell jobs have been removed due to secure loading
    if sys.platform != 'win32':
        assert len(jobs3) == 1


def test_load_config_yaml():
    config_file = os.path.join(TEST_DATA_DIR, 'urlwatch.yaml')
    if os.path.exists(config_file):
        config = YamlConfigStorage(config_file)
        assert config is not None
        assert config.config is not None
        assert config.config == storage.DEFAULT_CONFIG


def test_load_urls_txt():
    urls_txt = os.path.join(TEST_DATA_DIR, 'urls.txt')
    if os.path.exists(urls_txt):
        assert len(UrlsTxt(urls_txt).load_secure()) > 0


def test_load_urls_yaml():
    urls_yaml = os.path.join(REPO_ROOT, 'share/urlwatch/examples/urls.yaml.example')
    if os.path.exists(urls_yaml):
        assert len(UrlsYaml(urls_yaml).load_secure()) > 0


def test_load_hooks_py():
    hooks_py = os.path.join(REPO_ROOT, 'share/urlwatch/examples/hooks.py.example')
    if os.path.exists(hooks_py):
        imp.load_source('hooks', hooks_py)


def test_rapid_cache_change():
    with tempfile.TemporaryDirectory() as tempdir:
        cache = os.path.join(tempdir, 'cache.db')
        cache_storage = CacheMiniDBStorage2(cache)
        try:
            guid = binascii.hexlify(os.urandom(20)).decode()
            cache_storage.save(guid, 'first', time.time())
            cache_storage.save(guid, 'second', time.time())
            cache_storage.save(guid, 'last', time.time())
            snapshots = cache_storage.load(guid).snapshots
            print(snapshots)
            assert snapshots[0].data == 'last'
        finally:
            cache_storage.close()


def test_migrate_urls():
    with tempfile.TemporaryDirectory() as tempdir:
        urls_old_src = os.path.join(TEST_DATA_DIR, 'urls.txt')
        urls_old = os.path.join(tempdir, 'urls.txt')
        urls_new = os.path.join(tempdir, 'urls.yaml')
        shutil.copy2(urls_old_src, urls_old)

        old_data = {job.get_guid(): job.serialize() for job in UrlsTxt(urls_old).load_secure()}
        migrate_urls(TestConfig(tempdir))
        new_data = {job.get_guid(): job.serialize() for job in UrlsYaml(urls_new).load_secure()}

        assert old_data == new_data


def test_migrate_cache_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        old_cache_src = os.path.join(TEST_DATA_DIR, 'cache')
        old_cache = os.path.join(tempdir, 'cache')
        new_cache = os.path.join(tempdir, 'cache.db')
        shutil.copytree(old_cache_src, old_cache)

        old_cache_storage = CacheDirStorage(old_cache)
        old_data = {guid: old_cache_storage.load(guid, -1)
                    for guid in old_cache_storage.get_guids()}
        migrate_cache(TestConfig(tempdir))
        new_cache_storage = CacheMiniDBStorage2(new_cache)
        try:
            new_data = {guid: new_cache_storage.load(guid, -1)
                        for guid in new_cache_storage.get_guids()}
        finally:
            new_cache_storage.close()

        assert old_data == new_data


def test_migrate_cache_db():
    with tempfile.TemporaryDirectory() as tempdir:
        old_cache_src = os.path.join(TEST_DATA_DIR, 'cache.db')
        cache = os.path.join(tempdir, 'cache.db')
        shutil.copy2(old_cache_src, cache)

        old_cache_storage = CacheMiniDBStorage(cache)
        try:
            old_data = {guid: old_cache_storage.load(guid, -1)
                        for guid in old_cache_storage.get_guids()}
        finally:
            old_cache_storage.close()
        migrate_cache(TestConfig(tempdir))
        new_cache_storage = CacheMiniDBStorage2(cache)
        try:
            new_data = {guid: new_cache_storage.load(guid, -1)
                        for guid in new_cache_storage.get_guids()}
        finally:
            new_cache_storage.close()

        assert old_data == new_data
