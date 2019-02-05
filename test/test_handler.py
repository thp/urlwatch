import sys
import os
from glob import glob

import pycodestyle
from nose.tools import raises, with_setup

from urlwatch.jobs import JobBase, ShellJob
from urlwatch.config import BaseConfig
from urlwatch.main import Urlwatch


def test_required_classattrs_in_subclasses():
    for kind, subclass in JobBase.__subclasses__.items():
        assert hasattr(subclass, '__kind__')
        assert hasattr(subclass, '__required__')
        assert hasattr(subclass, '__optional__')


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

    urlwatch_config = TestConfig(config, urls, cache, hooks, True)
    urlwatcher = Urlwatch(urlwatch_config)
    try:
        urlwatcher.run_jobs()
    finally:
        urlwatcher.cache_storage.close()


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

    urlwatch_config = TestConfig(config, urls, cache, hooks, True)
    urlwatcher = Urlwatch(urlwatch_config)

    return urlwatcher


@with_setup(teardown=teardown_func)
def test_number_of_tries_in_cache_is_increased():
    urlwatcher = prepare_retry_test()
    try:
        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries
        assert tries == 0

        urlwatcher.run_jobs()
        urlwatcher.run_jobs()

        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries

        assert tries == 2
    finally:
        urlwatcher.cache_storage.close()


@with_setup(teardown=teardown_func)
def test_report_error_when_out_of_tries():
    urlwatcher = prepare_retry_test()
    try:
        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries
        assert tries == 0

        urlwatcher.run_jobs()
        urlwatcher.run_jobs()

        assert urlwatcher.report.job_states[-1].verb == 'error'
    finally:
        urlwatcher.cache_storage.close()


@with_setup(teardown=teardown_func)
def test_reset_tries_to_zero_when_successful():
    urlwatcher = prepare_retry_test()
    try:
        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries
        assert tries == 0

        urlwatcher.run_jobs()

        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries
        assert tries == 1

        # use an url that definitely exists
        job = urlwatcher.jobs[0]
        job.url = 'file://' + os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')

        urlwatcher.run_jobs()

        job = urlwatcher.jobs[0]
        tries = urlwatcher.cache_storage.load(job.get_guid()).tries
        assert tries == 0
    finally:
        urlwatcher.cache_storage.close()
