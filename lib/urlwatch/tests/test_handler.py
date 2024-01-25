import sys
from glob import glob

from urlwatch.jobs import UrlJob, JobBase, ShellJob
from urlwatch.storage import UrlsYaml, UrlsTxt

import contextlib
import pytest

import tempfile
import os

from urlwatch import storage
from urlwatch.config import CommandConfig
from urlwatch.storage import YamlConfigStorage, CacheMiniDBStorage
from urlwatch.main import Urlwatch
from urlwatch.util import import_module_from_source

root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
here = os.path.dirname(__file__)


def test_required_classattrs_in_subclasses():
    for kind, subclass in JobBase.__subclasses__.items():
        assert hasattr(subclass, '__kind__')
        assert hasattr(subclass, '__required__')
        assert hasattr(subclass, '__optional__')


def test_save_load_jobs():
    jobs = [
        UrlJob(name='news', url='http://news.orf.at/'),
        ShellJob(name='list homedir', command='ls ~'),
        ShellJob(name='list proc', command='ls /proc'),
    ]

    # tempfile.NamedTemporaryFile() doesn't work on Windows
    # because the returned file object cannot be opened again
    fd, name = tempfile.mkstemp()
    UrlsYaml(name).save(jobs)
    jobs2 = UrlsYaml(name).load()
    os.chmod(name, 0o777)
    jobs3 = UrlsYaml(name).load_secure()
    os.close(fd)
    os.remove(name)

    assert len(jobs2) == len(jobs)
    # Assert that the shell jobs have been removed due to secure loading
    if sys.platform != 'win32':
        assert len(jobs3) == 1


def test_load_config_yaml():
    config_file = os.path.join(here, 'data', 'urlwatch.yaml')
    if os.path.exists(config_file):
        config = YamlConfigStorage(config_file)
        assert config is not None
        assert config.config is not None
        assert config.config == storage.DEFAULT_CONFIG


def test_load_urls_txt():
    urls_txt = os.path.join(here, 'data', 'urls.txt')
    if os.path.exists(urls_txt):
        assert len(UrlsTxt(urls_txt).load_secure()) > 0


def test_load_urls_yaml():
    urls_yaml = 'share/urlwatch/examples/urls.yaml.example'
    if os.path.exists(urls_yaml):
        assert len(UrlsYaml(urls_yaml).load_secure()) > 0


def test_load_hooks_py():
    hooks_py = 'share/urlwatch/examples/hooks.py.example'
    if os.path.exists(hooks_py):
        import_module_from_source('hooks', hooks_py)


class ConfigForTest(CommandConfig):
    def __init__(self, config, urls, cache, hooks, verbose, args=()):
        super().__init__(args, 'urlwatch', os.path.dirname(__file__), root, config, urls, hooks, cache, verbose)


@contextlib.contextmanager
def teardown_func():
    try:
        yield
    finally:
        "tear down test fixtures"
        cache = os.path.join(here, 'data', 'cache.db')
        if os.path.exists(cache):
            os.remove(cache)


def test_run_watcher():
    with teardown_func():
        urls = os.path.join(root, 'share', 'urlwatch', 'examples', 'urls.yaml.example')
        config = os.path.join(here, 'data', 'urlwatch.yaml')
        cache = os.path.join(here, 'data', 'cache.db')
        hooks = ''

        config_storage = YamlConfigStorage(config)
        urls_storage = UrlsYaml(urls)
        cache_storage = CacheMiniDBStorage(cache)
        try:
            urlwatch_config = ConfigForTest(config, urls, cache, hooks, True)

            urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
            urlwatcher.run_jobs()
        finally:
            cache_storage.close()


def prepare_tags_test(args):
    urls = os.path.join(here, 'data', 'jobs-with-tags.yaml')
    config = os.path.join(here, 'data', 'urlwatch.yaml')
    cache = os.path.join(here, 'data', 'cache.db')
    hooks = ''

    config_storage = YamlConfigStorage(config)
    urls_storage = UrlsYaml(urls)
    cache_storage = CacheMiniDBStorage(cache)

    urlwatch_config = ConfigForTest(config, urls, cache, hooks, True, args=args)
    urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)

    return urlwatcher, cache_storage


def test_tags_none():
    with teardown_func():
        urlwatcher, cache_storage = prepare_tags_test([])
        try:
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 3
        finally:
            cache_storage.close()


def test_tags_empty():
    with teardown_func():
        urlwatcher, cache_storage = prepare_tags_test(['--tags'])
        try:
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 0
        finally:
            cache_storage.close()


def test_tags_no_match():
    with teardown_func():
        urlwatcher, cache_storage = prepare_tags_test(['--tags', 'foo'])
        try:
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 0
        finally:
            cache_storage.close()


def test_tags_single():
    with teardown_func():
        urlwatcher, cache_storage = prepare_tags_test(['--tags', 'arg'])
        try:
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 2
        finally:
            cache_storage.close()


def test_tags_multiple():
    with teardown_func():
        urlwatcher, cache_storage = prepare_tags_test(['--tags', 'utc', 'local'])
        try:
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 2
        finally:
            cache_storage.close()


def test_disabled_job():
    with teardown_func():
        urls = os.path.join(here, 'data', 'disabled-job.yaml')
        config = os.path.join(here, 'data', 'urlwatch.yaml')
        cache = os.path.join(here, 'data', 'cache.db')
        hooks = ''

        config_storage = YamlConfigStorage(config)
        urls_storage = UrlsYaml(urls)
        cache_storage = CacheMiniDBStorage(cache)
        try:
            urlwatch_config = ConfigForTest(config, urls, cache, hooks, True)

            urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
            urlwatcher.run_jobs()

            assert len(urlwatcher.report.job_states) == 1
        finally:
            cache_storage.close()


def test_unserialize_shell_job_without_kind():
    job = JobBase.unserialize({
        'name': 'hoho',
        'command': 'ls',
    })
    assert isinstance(job, ShellJob)


def test_unserialize_with_unknown_key():
    with pytest.raises(ValueError):
        JobBase.unserialize({
            'unknown_key': 123,
            'name': 'hoho',
        })


def prepare_retry_test():
    urls = os.path.join(here, 'data', 'invalid-url.yaml')
    config = os.path.join(here, 'data', 'urlwatch.yaml')
    cache = os.path.join(here, 'data', 'cache.db')
    hooks = ''

    config_storage = YamlConfigStorage(config)
    cache_storage = CacheMiniDBStorage(cache)
    urls_storage = UrlsYaml(urls)

    urlwatch_config = ConfigForTest(config, urls, cache, hooks, True)
    urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)

    return urlwatcher, cache_storage


def test_number_of_tries_in_cache_is_increased():
    with teardown_func():
        urlwatcher, cache_storage = prepare_retry_test()
        try:
            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
            assert tries == 0

            urlwatcher.run_jobs()
            urlwatcher.run_jobs()

            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())

            assert tries == 2
            assert urlwatcher.report.job_states[-1].verb == 'error'
        finally:
            cache_storage.close()


def test_report_error_when_out_of_tries():
    with teardown_func():
        urlwatcher, cache_storage = prepare_retry_test()
        try:
            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
            assert tries == 0

            urlwatcher.run_jobs()
            urlwatcher.run_jobs()

            report = urlwatcher.report
            assert report.job_states[-1].verb == 'error'
        finally:
            cache_storage.close()


def test_reset_tries_to_zero_when_successful():
    with teardown_func():
        urlwatcher, cache_storage = prepare_retry_test()
        try:
            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
            assert tries == 0

            urlwatcher.run_jobs()

            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
            assert tries == 1

            # use an url that definitely exists
            job = urlwatcher.jobs[0]
            job.url = 'file://' + os.path.join(here, 'data', 'urlwatch.yaml')

            urlwatcher.run_jobs()

            job = urlwatcher.jobs[0]
            old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
            assert tries == 0
        finally:
            cache_storage.close()
