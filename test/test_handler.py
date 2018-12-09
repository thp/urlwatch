import sys
from glob import glob

import pycodestyle as pycodestyle
from urlwatch.jobs import UrlJob, JobBase, ShellJob
from urlwatch.storage import UrlsYaml, UrlsTxt

from nose.tools import raises, with_setup

import tempfile
import os
import imp

from urlwatch import storage
from urlwatch.config import BaseConfig
from urlwatch.storage import YamlConfigStorage, CacheMiniDBStorage
from urlwatch.main import Urlwatch


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
    config_file = os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')
    if os.path.exists(config_file):
        config = YamlConfigStorage(config_file)
        assert config is not None
        assert config.config is not None
        assert config.config == storage.DEFAULT_CONFIG


def test_load_urls_txt():
    urls_txt = os.path.join(os.path.dirname(__file__), 'data', 'urls.txt')
    if os.path.exists(urls_txt):
        assert len(UrlsTxt(urls_txt).load_secure()) > 0


def test_load_urls_yaml():
    urls_yaml = 'share/urlwatch/examples/urls.yaml.example'
    if os.path.exists(urls_yaml):
        assert len(UrlsYaml(urls_yaml).load_secure()) > 0


def test_load_hooks_py():
    hooks_py = 'share/urlwatch/examples/hooks.py.example'
    if os.path.exists(hooks_py):
        imp.load_source('hooks', hooks_py)


def test_pep8_conformance():
    """Test that we conform to PEP-8."""
    style = pycodestyle.StyleGuide(ignore=['E501', 'E402', 'W503'])

    py_files = [y for x in os.walk(os.path.abspath('.')) for y in glob(os.path.join(x[0], '*.py'))]
    py_files.append(os.path.abspath('urlwatch'))
    result = style.check_files(py_files)
    assert result.total_errors == 0, "Found #{0} code style errors".format(result.total_errors)


class TestConfig(BaseConfig):
    def __init__(self, config, urls, cache, hooks, verbose):
        (prefix, bindir) = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))
        super().__init__('urlwatch', os.path.dirname(__file__), config, urls, cache, hooks, verbose)
        self.edit = False
        self.edit_hooks = False


def teardown_func():
    "tear down test fixtures"
    cache = os.path.join(os.path.dirname(__file__), 'data', 'cache.db')
    if os.path.exists(cache):
        os.remove(cache)


@with_setup(teardown=teardown_func)
def test_run_watcher():
    urls = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'share', 'urlwatch', 'examples', 'urls.yaml.example')
    config = os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')
    cache = os.path.join(os.path.dirname(__file__), 'data', 'cache.db')
    hooks = ''

    config_storage = YamlConfigStorage(config)
    urls_storage = UrlsYaml(urls)
    cache_storage = CacheMiniDBStorage(cache)
    try:
        urlwatch_config = TestConfig(config, urls, cache, hooks, True)

        urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
        urlwatcher.run_jobs()
    finally:
        cache_storage.close()


def test_unserialize_shell_job_without_kind():
    job = JobBase.unserialize({
        'name': 'hoho',
        'command': 'ls',
    })
    assert isinstance(job, ShellJob)


@raises(ValueError)
def test_unserialize_with_unknown_key():
    JobBase.unserialize({
        'unknown_key': 123,
        'name': 'hoho',
    })


def prepare_retry_test():
    urls = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test', 'data', 'invalid-url.yaml')
    config = os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')
    cache = os.path.join(os.path.dirname(__file__), 'data', 'cache.db')
    hooks = ''

    config_storage = YamlConfigStorage(config)
    cache_storage = CacheMiniDBStorage(cache)
    urls_storage = UrlsYaml(urls)

    urlwatch_config = TestConfig(config, urls, cache, hooks, True)
    urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)

    return urlwatcher, cache_storage


@with_setup(teardown=teardown_func)
def test_number_of_tries_in_cache_is_increased():
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


@with_setup(teardown=teardown_func)
def test_report_error_when_out_of_tries():
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


@with_setup(teardown=teardown_func)
def test_reset_tries_to_zero_when_successful():
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
        job.url = 'file://' + os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')

        urlwatcher.run_jobs()

        job = urlwatcher.jobs[0]
        old_data, timestamp, tries, etag = cache_storage.load(job, job.get_guid())
        assert tries == 0
    finally:
        cache_storage.close()
