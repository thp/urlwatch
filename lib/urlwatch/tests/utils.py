from unittest.mock import MagicMock


def setup_mock_playwright_response(html_content, status_code):
    mock_playwright = MagicMock()
    mock_playwright_instance = (
        mock_playwright.return_value.__enter__.return_value)

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
    mock_page.content.return_value = html_content
    return mock_playwright
