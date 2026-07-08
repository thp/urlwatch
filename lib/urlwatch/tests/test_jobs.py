from urlwatch.jobs import BrowserHttpError, BrowserJob, JobBase
from urlwatch.tests import utils

import contextlib

import pytest


@pytest.mark.parametrize('status_code, error_expected', [
    (300, True),
    (404, True),
    (200, False),
])
def test_browser_job_throws_http_error(
        monkeypatch, status_code, error_expected):
    mock_playwright = utils.setup_mock_playwright_response('', status_code)
    monkeypatch.setattr(
        'playwright.sync_api.sync_playwright', mock_playwright)

    job = JobBase.unserialize({
        'kind': 'browser',
        'navigate': 'https://www.example.com',
    })

    ctx_manager = contextlib.nullcontext()
    if error_expected:
        ctx_manager = pytest.raises(BrowserHttpError)
    with ctx_manager:
        job.retrieve(None)
