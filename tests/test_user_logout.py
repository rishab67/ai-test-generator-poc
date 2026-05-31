import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

def test_user_logout_success():
    """
    Tests the /user/logout endpoint for a successful logout.
    """
    # Assuming a user is already logged in for this test to be meaningful.
    # In a real scenario, you'd have a login test that sets up a session cookie
    # or token that this logout test would then use.
    # For this example, we'll simulate a successful request without explicit auth setup.
    # The Petstore API's logout endpoint doesn't require a specific payload or auth token
    # in its schema, but a real-world implementation likely would.

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(f"{BASE_URL}/user/logout", headers=headers)

    assert response.status_code == 200
    # The schema indicates 'successful operation' for default response,
    # which usually means a 200 OK. No specific response body is defined in the schema.
    # If the API returned a specific message on success, we'd assert that here.
    # For example:
    # assert response.json() == {"message": "logout successful"} # if such a response existed


# If the logout endpoint required specific headers or cookies from a prior login,
# a more robust test would involve:
# 1. A separate test for user login.
# 2. Storing session cookies or auth tokens from the login response.
# 3. Using those stored cookies/tokens in the logout request.

# Example of how you might structure that (not runnable without a login endpoint):
#
# @pytest.fixture(scope="session")
# def logged_in_session():
#     login_url = f"{BASE_URL}/user/login"
#     login_payload = {
#         "username": "testuser",
#         "password": "password123"
#     }
#     response = requests.post(login_url, json=login_payload)
#     response.raise_for_status() # Raise an exception for bad status codes
#     session = requests.Session()
#     session.cookies.update(response.cookies)
#     yield session
#
# def test_user_logout_with_session(logged_in_session):
#     logout_url = f"{BASE_URL}/user/logout"
#     response = logged_in_session.get(logout_url, headers={"Accept": "application/json"})
#     assert response.status_code == 200