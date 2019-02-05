import sys
import os
import tempfile
import time
from glob import glob

import pycodestyle
from nose.tools import raises

from urlwatch.jobs import JobBase, UrlJob, ShellJob
from urlwatch.storage import UrlsYaml

from util import default_watcher, TEST_DATA_DIR, REPO_ROOT


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


def test_run_watcher():
    with default_watcher(urls=os.path.join(REPO_ROOT,
                         'share/urlwatch/examples/urls.yaml.example')) as urlwatcher:
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


def test_retries():
    with tempfile.TemporaryDirectory() as tempdir:
        # save a url job with a valid local url but an invalid filter
        urls = os.path.join(tempdir, 'urls.yaml')
        local_url = 'file://' + os.path.join(TEST_DATA_DIR, 'urlwatch.yaml')
        urls_storage = UrlsYaml(urls)
        urls_storage.save([UrlJob(url=local_url, filter='invalid-filter', max_tries=2)])

        guid = urls_storage.load_secure()[0].get_guid()
        with default_watcher(tempdir) as urlwatcher:
            assert urlwatcher.cache_storage.load(guid).tries == 0
            urlwatcher.run_jobs()
            assert len(urlwatcher.report.job_states) == 0
        with default_watcher(tempdir) as urlwatcher:
            assert urlwatcher.cache_storage.load(guid).tries == 1
            urlwatcher.run_jobs()
            assert len(urlwatcher.report.job_states) == 1
            assert urlwatcher.report.job_states[0].verb == 'error'

        # remove the invalid filter but keep the same local url (hence guid)
        urls_storage.save([UrlJob(url=local_url, max_tries=2)])

        with default_watcher(tempdir) as urlwatcher:
            assert urlwatcher.cache_storage.load(guid).tries == 2
            urlwatcher.run_jobs()
            assert len(urlwatcher.report.job_states) == 1
            assert urlwatcher.report.job_states[0].verb == 'new'
            assert urlwatcher.cache_storage.load(guid).tries == 0


def test_compare_multiple_snapshots():
    with tempfile.TemporaryDirectory() as tempdir:
        # save a url job with a local url
        urls = os.path.join(tempdir, 'urls.yaml')
        data_file_path = os.path.join(tempdir, 'data_file')
        local_url = 'file://' + data_file_path
        urls_storage = UrlsYaml(urls)
        urls_storage.save([UrlJob(url=local_url, compared_versions=2)])

        # prepare a history of three different snapshots
        with default_watcher(tempdir) as urlwatcher:
            with open(data_file_path, 'w') as f:
                f.write('version-1')
            urlwatcher.run_jobs()
            time.sleep(1.01)
            with open(data_file_path, 'w') as f:
                f.write('version-2')
            urlwatcher.run_jobs()
            time.sleep(1.01)
            with open(data_file_path, 'w') as f:
                f.write('version-3')
            urlwatcher.run_jobs()

        # a reversion to within last 2 snapshots does not count as a change
        with default_watcher(tempdir) as urlwatcher:
            with open(data_file_path, 'w') as f:
                f.write('version-2')
            urlwatcher.run_jobs()
            assert len(urlwatcher.report.job_states) == 1
            assert urlwatcher.report.job_states[0].verb == 'unchanged'

        # a reversion to before the last 2 snapshots counts as a change
        with default_watcher(tempdir) as urlwatcher:
            with open(data_file_path, 'w') as f:
                f.write('version-1')
            urlwatcher.run_jobs()
            assert len(urlwatcher.report.job_states) == 1
            assert urlwatcher.report.job_states[0].verb == 'changed'
