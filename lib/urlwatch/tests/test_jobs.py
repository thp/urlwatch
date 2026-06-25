from urlwatch.jobs import BrowserHttpError, BrowserJob, JobBase

import contextlib
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize("raise_for_status,status_code,error_expected", [
    (True, 404, True),
    (True, 200, False),
    (False, 500, False),
    (False, 200, False),
    (None, 403, False),
    (None, 200, False),
])
def test_browser_job_throws_http_error_if_enabled(
        monkeypatch, raise_for_status, status_code, error_expected):
    mock_sync_playwright = MagicMock()
    mock_playwright_instance = (
        mock_sync_playwright.return_value.__enter__.return_value)

    mock_browser_type = MagicMock()
    mock_playwright_instance.__getitem__.return_value = mock_browser_type

    mock_browser = MagicMock()
    mock_browser_type.launch.return_value = mock_browser

    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_response = MagicMock()
    # Playwright counts 200 - 299 as ok since the browser handles redirects.
    # https://playwright.dev/python/docs/api/class-response#response-ok
    mock_response.ok = status_code >= 200 and status_code <= 299
    mock_response.status = status_code
    mock_page.goto.return_value = mock_response

    monkeypatch.setattr(
        "playwright.sync_api.sync_playwright", mock_sync_playwright)

    job = JobBase.unserialize({
        'kind': 'browser',
        'navigate': 'https://www.example.com',
        'raise_for_status': raise_for_status
    })

    ctx_manager = contextlib.nullcontext()
    if error_expected:
        ctx_manager = pytest.raises(BrowserHttpError)
    with ctx_manager:
        job.retrieve(None)
