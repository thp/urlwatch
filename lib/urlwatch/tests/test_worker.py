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


class ConfigForTest(CommandConfig):
    def __init__(self, config, urls, cache, hooks, verbose):
        super().__init__([], 'urlwatch', os.path.dirname(__file__), root, config, urls, hooks, cache, verbose)


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
        urls = os.path.join(here, 'data', 'disabled-job.yaml')
        config = os.path.join(here, 'data', 'urlwatch.yaml')
        cache = os.path.join(here, 'data', 'cache.db')
        hooks = ''

        config_storage = YamlConfigStorage(config)
        urls_storage = UrlsYaml(urls)
        cache_storage = CacheMiniDBStorage(cache)
        try:
            urlwatch_config = ConfigForTest(config, urls, cache, hooks, True)

            # Prime cache
            urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
            urlwatcher.run_jobs()

            # Run multiple times with clean report
            for _ in range(100):
                urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
                urlwatcher.run_jobs()
                for job_state in urlwatcher.report.job_states:
                    assert job_state.exception is None, 'Job failed during threading test'
                    assert job_state.verb == 'unchanged', f'Job verb was "{job_state.verb}" for unchanged output during threading test'
        finally:
            cache_storage.close()
