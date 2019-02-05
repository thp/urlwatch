import os
import tempfile
from contextlib import contextmanager

from urlwatch.config import BaseConfig
from urlwatch.main import Urlwatch


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TEST_DIR)
TEST_DATA_DIR = os.path.join(TEST_DIR, 'data')


class TestConfig(BaseConfig):
    def __init__(self, urlwatch_dir, config=None, urls=None, cache=None, hooks='', verbose=True):
        if config is None:
            config = os.path.join(TEST_DATA_DIR, 'urlwatch.yaml')
        if urls is None:
            urls = os.path.join(urlwatch_dir, 'urls.yaml')
        if cache is None:
            cache = os.path.join(urlwatch_dir, 'cache.db')
        super().__init__('urlwatch', urlwatch_dir, config, urls, cache, hooks, verbose)
        self.edit = False
        self.edit_hooks = False


@contextmanager
def default_watcher(urlwatch_dir=None, config=None, urls=None, cache=None, hooks='', verbose=True):
    tempdir = None
    if urlwatch_dir is None:
        tempdir = tempfile.TemporaryDirectory()
        urlwatch_dir = tempdir.name
    urlwatch_config = TestConfig(urlwatch_dir, config, urls, cache, hooks, verbose)
    urlwatcher = Urlwatch(urlwatch_config)
    try:
        yield urlwatcher
    finally:
        urlwatcher.cache_storage.close()
        if tempdir is not None:
            tempdir.cleanup()
