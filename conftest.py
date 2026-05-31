import pytest
from playwright.sync_api import Playwright, APIRequestContext

# This is the exact fixture the AI was looking for!
@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright) -> APIRequestContext:
    # We will point it at a free public testing API
    request_context = playwright.request.new_context(base_url="https://reqres.in")
    yield request_context
    request_context.dispose()