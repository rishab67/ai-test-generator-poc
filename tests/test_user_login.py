import requests
import pytest
from datetime import datetime
import re

# STRICT RULE: The BASE_URL must be hardcoded as: "https://petstore.swagger.io/v2"
BASE_URL = "https://petstore.swagger.io/v2"
LOGIN_ENDPOINT = f"{BASE_URL}/user/login"

# Helper for validating ISO 8601 date-time format for X-Expires-After header
# Covers YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS.sss+/-HH:MM
DATE_TIME_REGEX = r'^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(\.[0-9]+)?(Z|([+\-])([0-9]{2}):([0-9]{2}))?$'


@pytest.fixture(scope="module")
def api_client():
    """Provides a requests session for all tests."""
    with requests.Session() as session:
        yield session


def test_positive_login_200_ok(api_client):
    """
    1. [Positive] 200 OK with a perfect, complete payload.
    Logs user into the system with valid credentials.
    """
    params = {
        "username": "user",  # Common Petstore demo username
        "password": "password"  # Common Petstore demo password
    }
    response = api_client.get(LOGIN_ENDPOINT, params=params)

    assert response.status_code == 200, \
        f"Expected status code 200 but got {response.status_code}. Response: {response.text}"
    
    # Assert response body is a string (token)
    assert isinstance(response.text, str), "Response body should be a string token."
    assert len(response.text) > 0, "Response token should not be empty."

    # Assert X-Expires-After header
    expires_after = response.headers.get("X-Expires-After")
    assert expires_after is not None, "X-Expires-After header is missing."
    assert re.match(DATE_TIME_REGEX, expires_after), \
        f"X-Expires-After header '{expires_after}' is not in valid ISO 8601 date-time format."
    
    # Assert X-Rate-Limit header
    rate_limit = response.headers.get("X-Rate-Limit")
    assert rate_limit is not None, "X-Rate-Limit header is missing."
    try:
        rate_limit_int = int(rate_limit)
        assert rate_limit_int >= 0, "X-Rate-Limit should be a non-negative integer."
    except ValueError:
        pytest.fail(f"X-Rate-Limit header '{rate_limit}' is not a valid integer or missing.")


@pytest.mark.parametrize("test_case_name, params", [
    ("missing_username", {"password": "password"}),
    ("missing_password", {"username": "user"}),
    ("missing_both", {}),
])
def test_negative_login_400_missing_required_fields(api_client, test_case_name, params):
    """
    2. [Negative] 400 Invalid input (missing required fields).
    Tests login attempts with missing username or password.
    """
    response = api_client.get(LOGIN_ENDPOINT, params=params)

    assert response.status_code == 400, \
        f"Expected status code 400 for {test_case_name} but got {response.status_code}. Response: {response.text}"
    assert "Invalid username/password supplied" in response.text, \
        f"Expected error message 'Invalid username/password supplied' for {test_case_name} but got: {response.text}"


@pytest.mark.parametrize("test_case_name, params", [
    ("username_int", {"username": 123, "password": "password"}),
    ("password_int", {"username": "user", "password": 456}),
    ("username_empty", {"username": "", "password": "password"}),
    ("password_empty", {"username": "user", "password": ""}),
    ("username_special_chars", {"username": "<script>alert(1)</script>", "password": "password"}),
    ("password_sql_injection", {"username": "user", "password": "' OR '1'='1"}),
    ("long_username", {"username": "a" * 256, "password": "password"}), # Example of length boundary
    ("long_password", {"username": "user", "password": "b" * 256}), # Example of length boundary
])
def test_negative_login_400_boundary_invalid_input(api_client, test_case_name, params):
    """
    3. [Negative] 400 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    Tests login attempts with invalid data types or boundary values for username/password.
    """
    response = api_client.get(LOGIN_ENDPOINT, params=params)

    # For query parameters, `requests` library automatically converts integer values to strings.
    # The API's behavior for these stringified integers depends on its backend validation.
    # We assert for 400 as the general "invalid input" response based on the schema.
    assert response.status_code == 400, \
        f"Expected status code 400 for {test_case_name} but got {response.status_code}. Response: {response.text}"
    assert "Invalid username/password supplied" in response.text, \
        f"Expected error message 'Invalid username/password supplied' for {test_case_name} but got: {response.text}"


def test_security_login_401_403_unauthorized(api_client):
    """
    4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    
    NOTE: The OpenAPI schema for this '/user/login' endpoint only defines a 400 response for
    'Invalid username/password supplied' when credentials are provided in query parameters.
    It does not explicitly specify any required *authentication headers* for *accessing* the
    login endpoint itself.

    However, as a Principal API SDET and Security Tester, we simulate scenarios where an
    underlying API Gateway or other security layers might reject a request *before* it
    reaches the specific login logic that would return a 400. This test strictly asserts
    for 401 or 403 status codes, which would indicate such an external security control.
    """
    
    # Scenario: Attempt to access the login endpoint without any required query parameters
    # and with a common, but invalid/bogus, Authorization header. This simulates a request
    # that an API Gateway might reject if it expects some form of global authorization or token
    # even for a login attempt.
    headers = {"Authorization": "Bearer not_a_real_token_123"}
    response = api_client.get(LOGIN_ENDPOINT, headers=headers)

    # We are strictly looking for 401 (Unauthorized) or 403 (Forbidden) as per the test case requirement.
    # If the API returns 400 (as the Petstore API often does for missing query parameters),
    # it implies that the request bypassed any potential gateway-level 401/403 checks
    # and reached the application logic that validates the login query parameters.
    assert response.status_code in [401, 403], \
        f"Expected status code 401 or 403 for unauthorized access attempt (missing credentials, bogus auth header) " \
        f"but got {response.status_code}. Response: {response.text}"