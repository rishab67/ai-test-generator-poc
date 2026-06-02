import pytest
import requests
import json

BASE_URL = "https://petstore.swagger.io/v2"
LOGOUT_ENDPOINT = "/user/logout"

@pytest.fixture(scope="function")
def api_session():
    """Provides a requests session for tests, ensuring a clean state for each test."""
    session = requests.Session()
    yield session
    session.close()

def clear_session_cookies(session):
    """Helper function to clear all cookies from a session."""
    session.cookies.clear()

def test_positive_logout_200_ok(api_session):
    """
    [Positive] Test case for successful user logout, expecting a 200 OK status.
    This simulates a perfect request without any extra parameters, assuming an active session.
    """
    url = f"{BASE_URL}{LOGOUT_ENDPOINT}"
    
    # Simulate a login to ensure a session cookie is present, making the logout more realistic.
    # The Petstore API's /user/logout is often idempotent, returning 200 even without an active session.
    login_url = f"{BASE_URL}/user/login"
    login_params = {"username": "testuser", "password": "password123"}
    try:
        api_session.get(login_url, params=login_params)
    except requests.exceptions.RequestException:
        pass # Ignore login failures for this test, as logout behavior is often idempotent.

    response = api_session.get(url)

    assert response.status_code == 200, \
        f"Expected status code 200 for successful logout, but got {response.status_code}. Response: {response.text}"
    
    content_type = response.headers.get('Content-Type', '')
    if 'application/json' in content_type:
        try:
            response_json = response.json()
            assert response_json == {} or (isinstance(response_json, dict) and "message" in response_json), \
                f"Expected empty JSON object or a dict with 'message', but got: {response_json}"
        except json.JSONDecodeError:
            assert response.text == "" or response.text.lower() == "ok", \
                f"Expected empty or 'ok' string for JSON content-type but invalid JSON, got: '{response.text}'"
    elif 'application/xml' in content_type:
        assert response.text == "" or "<message>ok</message>" in response.text.lower(), \
            f"Expected empty or simple XML response, but got: {response.text}"
    else:
        assert response.text == "" or response.text.lower() == "ok", \
            f"Expected empty or 'ok' string response, but got: '{response.text}'"

def test_negative_logout_invalid_input_with_body(api_session):
    """
    [Negative] Test case for invalid input, specifically sending a request body with a GET request.
    Expects 400 Bad Request or 405 Method Not Allowed.
    """
    url = f"{BASE_URL}{LOGOUT_ENDPOINT}"
    invalid_payload = {"some_key": "some_value"}
    
    response = api_session.get(url, json=invalid_payload)

    assert response.status_code in [400, 405], \
        f"Expected status code 400 or 405 for invalid input (body with GET), but got {response.status_code}. Response: {response.text}"
    
    error_message_found = False
    try:
        error_json = response.json()
        if "message" in error_json and ("bad request" in error_json["message"].lower() or "not allowed" in error_json["message"].lower()):
            error_message_found = True
        elif "code" in error_json and error_json["code"] in [400, 405]:
             error_message_found = True
    except json.JSONDecodeError:
        if "bad request" in response.text.lower() or "not allowed" in response.text.lower() or "unsupported method" in response.text.lower():
            error_message_found = True
    
    assert error_message_found, \
        f"Expected error message indicating bad request or method not allowed, but got: {response.text}"

def test_negative_logout_unsupported_method(api_session):
    """
    [Negative] Test case for boundary testing by using unsupported HTTP methods (e.g., POST, PUT).
    Expects 405 Method Not Allowed.
    """
    url = f"{BASE_URL}{LOGOUT_ENDPOINT}"
    
    response = api_session.post(url)
    assert response.status_code == 405, \
        f"Expected status code 405 for unsupported method (POST), but got {response.status_code}. Response: {response.text}"
    
    error_message_found = False
    try:
        error_json = response.json()
        if "message" in error_json and "method not allowed" in error_json["message"].lower():
            error_message_found = True
        elif "code" in error_json and error_json["code"] == 405:
            error_message_found = True
    except json.JSONDecodeError:
        if "method not allowed" in response.text.lower():
            error_message_found = True
    assert error_message_found, \
        f"Expected error message 'Method Not Allowed' for POST, but got: {response.text}"

    response = api_session.put(url)
    assert response.status_code == 405, \
        f"Expected status code 405 for unsupported method (PUT), but got {response.status_code}. Response: {response.text}"
    
    error_message_found = False
    try:
        error_json = response.json()
        if "message" in error_json and "method not allowed" in error_json["message"].lower():
            error_message_found = True
        elif "code" in error_json and error_json["code"] == 405:
            error_message_found = True
    except json.JSONDecodeError:
        if "method not allowed" in response.text.lower():
            error_message_found = True
    assert error_message_found, \
        f"Expected error message 'Method Not Allowed' for PUT, but got: {response.text}"

def test_security_logout_unauthorized_no_session(api_session):
    """
    [Security] Test case for unauthorized logout due to a missing session.
    Expects 401 Unauthorized or 403 Forbidden.
    """
    url = f"{BASE_URL}{LOGOUT_ENDPOINT}"
    
    clear_session_cookies(api_session)

    response = api_session.get(url)

    assert response.status_code in [401, 403], \
        f"SECURITY ISSUE: Expected status code 401 or 403 for unauthorized logout (no session), but got {response.status_code}. " \
        f"This may indicate the API logs out even without an active session, which could be an information disclosure if response implies 'success'." \
        f"Response: {response.text}"

def test_security_logout_unauthorized_invalid_session(api_session):
    """
    [Security] Test case for unauthorized logout due to an invalid session cookie.
    Expects 401 Unauthorized or 403 Forbidden.
    """
    url = f"{BASE_URL}{LOGOUT_ENDPOINT}"

    api_session.cookies.set('JSESSIONID', 'invalid_session_id_12345', domain='petstore.swagger.io', path='/v2')

    response = api_session.get(url)

    assert response.status_code in [401, 403], \
        f"SECURITY ISSUE: Expected status code 401 or 403 for unauthorized logout (invalid session), but got {response.status_code}. " \
        f"This may indicate the API logs out even with an invalid session cookie, which could be an information disclosure if response implies 'success'." \
        f"Response: {response.text}"