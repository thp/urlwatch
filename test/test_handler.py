from urlwatch.handler import *

from nose.tools import *

import tempfile
import os


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
        jobs3 = UrlsYaml(tmp.name).load_secure()

    assert len(jobs2) == len(jobs)
    # Assert that the shell jobs have been removed due to secure loading
    assert len(jobs3) == 1


def test_load_examples():
    txt_jobs = UrlsTxt(os.path.join(os.path.dirname(__file__), 'data', 'urls.txt')).load_secure()
    assert len(txt_jobs) > 0

    yaml_jobs = UrlsYaml('share/urlwatch/examples/urls.yaml.example').load_secure()
    assert len(yaml_jobs) > 0


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
