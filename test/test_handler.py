import sys
from glob import glob

import pycodestyle as pycodestyle
from urlwatch.jobs import UrlJob, JobBase, ShellJob
from urlwatch.storage import UrlsYaml, UrlsTxt

from nose.tools import raises, with_setup

import tempfile
import os
import imp

from lib.urlwatch import storage
from lib.urlwatch.config import BaseConfig
from lib.urlwatch.storage import JsonConfigStorage, YamlConfigStorage, UrlsJson, CacheMiniDBStorage
from lib.urlwatch.main import Urlwatch


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

    with tempfile.NamedTemporaryFile() as tmp:
        UrlsYaml(tmp.name).save(jobs)
        jobs2 = UrlsYaml(tmp.name).load()
        os.chmod(tmp.name, 0o777)
        jobs3 = UrlsYaml(tmp.name).load_secure()

    assert len(jobs2) == len(jobs)
    # Assert that the shell jobs have been removed due to secure loading
    assert len(jobs3) == 1


def test_load_config_yaml():
    config_json = os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.yaml')
    if os.path.exists(config_json):
        config = YamlConfigStorage(config_json)
        assert config is not None
        assert config.config is not None
        assert config.config == storage.DEFAULT_CONFIG


def test_load_config_json():
    config_json = os.path.join(os.path.dirname(__file__), 'data', 'urlwatch.json')
    if os.path.exists(config_json):
        config = JsonConfigStorage(config_json)
        assert config is not None
        assert config.config is not None
        assert config.config == storage.DEFAULT_CONFIG


def test_load_urls_txt():
    urls_txt = os.path.join(os.path.dirname(__file__), 'data', 'urls.txt')
    if os.path.exists(urls_txt):
        assert len(UrlsTxt(urls_txt).load_secure()) > 0


def test_load_urls_json():
    urls_txt = os.path.join(os.path.dirname(__file__), 'data', 'urls.json')
    if os.path.exists(urls_txt):
        assert len(UrlsJson(urls_txt).load_secure()) > 0


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
    style = pycodestyle.StyleGuide(ignore=['E501', 'E402'])

    py_files = [y for x in os.walk(os.path.abspath('.')) for y in glob(os.path.join(x[0], '*.py'))]
    py_files.append(os.path.abspath('urlwatch'))
    result = style.check_files(py_files)
    assert result.total_errors == 0, "Found #{0} code style errors".format(result.total_errors)


class TestConfig(BaseConfig):
    def __init__(self, config, urls, cache, hooks, verbose):
        (prefix, bindir) = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))
        super().__init__('urlwatch', os.path.dirname(__file__), config, urls, cache, hooks, verbose)


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
    cache_storage = CacheMiniDBStorage(cache)
    urls_storage = UrlsYaml(urls)

    urlwatch_config = TestConfig(config, urls, cache, hooks, True)

    urlwatcher = Urlwatch(urlwatch_config, config_storage, cache_storage, urls_storage)
    urlwatcher.run_jobs()


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
