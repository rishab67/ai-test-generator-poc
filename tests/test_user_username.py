import pytest
import requests
import json
import uuid

BASE_URL = "https://petstore.swagger.io/v2"

# --- Helper Functions and Fixtures ---

@pytest.fixture(scope="module")
def api_key_header():
    """Fixture for simulating an API key for 'logged in' operations."""
    # The Petstore API typically uses 'api_key' header for certain operations,
    # or sometimes implicit session. For general "logged in user" scenarios,
    # a standard Authorization header with a Bearer token is a good simulation.
    # The actual Petstore v2 does not enforce strict auth for /user updates/deletes
    # without a specific security definition, so these 401/403 tests might
    # pass with 200/404 if the API allows it, but we test against the *schema description*.
    return {"Authorization": "Bearer some-dummy-jwt-token"}

@pytest.fixture(scope="function")
def test_username():
    """Generates a unique username for each test function that needs to create a user."""
    return f"test_user_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="function")
def setup_user(test_username, api_key_header):
    """
    Creates a user before a test and deletes it afterwards.
    Yields the username and the full user data.
    """
    user_data = {
        "id": 0,
        "username": test_username,
        "firstName": "John",
        "lastName": "Doe",
        "email": f"{test_username}@example.com",
        "password": "password123",
        "phone": "123-456-7890",
        "userStatus": 1
    }
    
    # Create the user using POST /user (assumed to be available for setup)
    create_url = f"{BASE_URL}/user"
    headers = {"Content-Type": "application/json"}
    # Petstore's POST /user often doesn't require auth, but including it just in case
    headers.update(api_key_header) 
    
    response = requests.post(create_url, headers=headers, data=json.dumps(user_data))
    
    # Assert successful creation for setup purposes, or if user already exists due to specific test conditions
    assert response.status_code in [200, 409], f"Failed to create user for setup: {response.status_code} - {response.text}"
    
    yield test_username, user_data

    # Teardown: Delete the user
    delete_url = f"{BASE_URL}/user/{test_username}"
    delete_headers = api_key_header
    
    response = requests.delete(delete_url, headers=delete_headers)
    
    # Assert successful deletion for teardown purposes, or note if already deleted by test
    assert response.status_code in [200, 204, 404], f"Failed to delete user {test_username} during teardown: {response.status_code} - {response.text}"

# --- GET /user/{username} Tests ---

class TestGetUserByUsername:
    """Tests for GET /user/{username} endpoint."""

    # 1. [Positive] 200 OK with a perfect, complete payload.
    def test_get_user_positive_perfect_payload(self, setup_user):
        """
        Tests fetching an existing user with a valid username, expecting 200 OK.
        Verifies the response structure and data consistency.
        """
        username, initial_user_data = setup_user
        
        url = f"{BASE_URL}/user/{username}"
        response = requests.get(url)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
        response_data = response.json()

        assert isinstance(response_data, dict), "Response data should be a dictionary."
        assert "id" in response_data
        assert "username" in response_data
        assert "firstName" in response_data
        assert "lastName" in response_data
        assert "email" in response_data
        assert "password" in response_data # Password might be returned or masked; presence is checked.
        assert "phone" in response_data
        assert "userStatus" in response_data

        assert response_data["username"] == initial_user_data["username"]
        assert response_data["email"] == initial_user_data["email"]
        assert response_data["firstName"] == initial_user_data["firstName"]
        assert response_data["userStatus"] == initial_user_data["userStatus"]
        # Password might be returned as 'string' or actual value, or omitted.
        # If it's a string, we assume it's the one we sent or a placeholder.
        if isinstance(response_data.get("password"), str) and response_data["password"]:
            # Petstore often returns 'password' as 'string' if not set properly,
            # or the actual password if stored plain. We check if it's there.
            pass

    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    # Part 1: Non-existent username -> 404
    def test_get_user_negative_not_found(self):
        """Tests fetching a non-existent user, expecting a 404 Not Found."""
        non_existent_username = "non_existent_user_" + uuid.uuid4().hex[:8]
        url = f"{BASE_URL}/user/{non_existent_username}"
        response = requests.get(url)

        assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}. Response: {response.text}"

    # Part 2: Invalid username formats -> 400/404
    @pytest.mark.parametrize("invalid_username", [
        "",  # Empty string (path parameter may lead to malformed URL or 404)
        "   ", # Whitespace string
        "12345", # Integer-like string (Petstore might treat as valid username)
        "!@#$%^&*()", # Special characters (Petstore might treat as valid username, or 404)
        "a" * 256 # Extremely long name (boundary for string length)
    ])
    def test_get_user_negative_invalid_username_format(self, invalid_username):
        """
        Tests fetching with invalid username formats in the path parameter.
        Expects 400 (Invalid username supplied) or 404 (User not found).
        """
        # For an empty string, requests.get(f"{BASE_URL}/user/") might hit a different endpoint or error.
        # Directly including it in the path: f"{BASE_URL}/user/" + "" = f"{BASE_URL}/user/"
        # which usually results in 404 on Petstore, or 400 for invalid URI.
        url = f"{BASE_URL}/user/{invalid_username}"
        response = requests.get(url)

        # Petstore often returns 404 for non-matching usernames, even if technically malformed.
        # According to spec, 400 for 'Invalid username supplied' is also possible.
        assert response.status_code in [400, 404], \
            f"Expected 400 or 404 for username '{invalid_username}', got {response.status_code}. Response: {response.text}"


# --- PUT /user/{username} Tests ---

class TestUpdateUserByUsername:
    """Tests for PUT /user/{username} endpoint."""

    # 1. [Positive] 200 OK with a perfect, complete payload.
    def test_put_user_positive_perfect_payload(self, setup_user, api_key_header):
        """
        Tests updating an existing user with a valid username and a complete, valid payload.
        Verifies the update by fetching the user afterwards.
        """
        username, initial_user_data = setup_user
        
        updated_data = initial_user_data.copy()
        updated_data["firstName"] = "Jane"
        updated_data["lastName"] = "Smith"
        updated_data["email"] = f"jane.smith.{username}@example.com"
        updated_data["userStatus"] = 2 # Changed status
        # It's important to keep the username in the body consistent if the API expects it,
        # even if it's typically ignored for path-based updates.
        updated_data["username"] = username 

        url = f"{BASE_URL}/user/{username}"
        headers = {"Content-Type": "application/json"}
        headers.update(api_key_header)

        response = requests.put(url, headers=headers, data=json.dumps(updated_data))
        
        # OpenAPI spec for PUT /user/{username} only explicitly lists 400/404,
        # but a successful update typically returns 200 OK or 204 No Content.
        # Petstore's implementation generally returns 200 OK.
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
        
        # Verify the update by fetching the user again
        get_response = requests.get(url)
        assert get_response.status_code == 200, f"Failed to fetch updated user for verification: {get_response.text}"
        fetched_data = get_response.json()

        assert fetched_data["firstName"] == updated_data["firstName"]
        assert fetched_data["email"] == updated_data["email"]
        assert fetched_data["userStatus"] == updated_data["userStatus"]
        assert fetched_data["username"] == username
        assert fetched_data["lastName"] == updated_data["lastName"]

    # 2. [Negative] 400/405 Invalid input (missing required fields in body).
    def test_put_user_negative_missing_required_fields_in_body(self, setup_user, api_key_header):
        """
        Tests updating a user with a payload missing critical fields (e.g., username, email etc.).
        Expects 400 (Invalid user supplied).
        """
        username, _ = setup_user
        
        malformed_data = {
            "firstName": "Partial",
            # Missing username, email, password, etc. which are usually part of the User definition
        }

        url = f"{BASE_URL}/user/{username}"
        headers = {"Content-Type": "application/json"}
        headers.update(api_key_header)

        response = requests.put(url, headers=headers, data=json.dumps(malformed_data))
        
        # OpenAPI spec indicates 400 for "Invalid user supplied".
        assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}. Response: {response.text}"

    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    # Part 1: Non-existent user for update -> 404
    def test_put_user_negative_not_found(self, api_key_header):
        """Tests updating a non-existent user, expecting a 404 Not Found."""
        non_existent_username = "non_existent_user_for_update_" + uuid.uuid4().hex[:8]
        user_data = {
            "id": 0,
            "username": non_existent_username,
            "firstName": "Ghost",
            "lastName": "User",
            "email": "ghost@example.com",
            "password": "password",
            "phone": "000",
            "userStatus": 0
        }

        url = f"{BASE_URL}/user/{non_existent_username}"
        headers = {"Content-Type": "application/json"}
        headers.update(api_key_header)

        response = requests.put(url, headers=headers, data=json.dumps(user_data))

        assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}. Response: {response.text}"

    # Part 2: Invalid username format in path parameter -> 400/404
    @pytest.mark.parametrize("invalid_path_username", [
        "",  # Empty string
        "   ", # Whitespace string
        "!@#$%^&*()", # Special characters
        "a" * 256 # Extremely long name
    ])
    def test_put_user_negative_invalid_path_username_format(self, api_key_header, invalid_path_username):
        """
        Tests updating with invalid username formats in the path parameter.
        Expects 400 (Invalid user supplied) or 404 (User not found).
        """
        dummy_user_data = { # A valid body is still needed
            "id": 1,
            "username": "dummy_for_invalid_path",
            "firstName": "Dummy",
            "lastName": "User",
            "email": "dummy@example.com",
            "password": "pass",
            "phone": "123",
            "userStatus": 1
        }

        url = f"{BASE_URL}/user/{invalid_path_username}"
        headers = {"Content-Type": "application/json"}
        headers.update(api_key_header)

        response = requests.put(url, headers=headers, data=json.dumps(dummy_user_data))
        
        assert response.status_code in [400, 404], \
            f"Expected 400 or 404 for username '{invalid_path_username}', got {response.status_code}. Response: {response.text}"
    
    # 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    def test_put_user_security_unauthorized_missing_header(self, setup_user):
        """
        Tests updating a user without authentication headers, expecting 401 Unauthorized or 403 Forbidden.
        The spec states: "This can only be done by the logged in user."
        """
        username, initial_user_data = setup_user
        
        updated_data = initial_user_data.copy()
        updated_data["firstName"] = "Unauthorized Attempt"
        updated_data["username"] = username

        url = f"{BASE_URL}/user/{username}"
        headers = {"Content-Type": "application/json"} # No API key/Authorization header

        response = requests.put(url, headers=headers, data=json.dumps(updated_data))
        
        assert response.status_code in [401, 403], \
            f"Expected 401 or 403 for unauthorized PUT, got {response.status_code}. Response: {response.text}"

    def test_put_user_security_unauthorized_invalid_header(self, setup_user):
        """
        Tests updating a user with an invalid authentication header, expecting 401 Unauthorized or 403 Forbidden.
        """
        username, initial_user_data = setup_user
        
        updated_data = initial_user_data.copy()
        updated_data["firstName"] = "InvalidAuth Attempt"
        updated_data["username"] = username

        url = f"{BASE_URL}/user/{username}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid-jwt-token-123" # Invalid token simulation
        }

        response = requests.put(url, headers=headers, data=json.dumps(updated_data))
        
        assert response.status_code in [401, 403], \
            f"Expected 401 or 403 for invalid auth PUT, got {response.status_code}. Response: {response.text}"


# --- DELETE /user/{username} Tests ---

class TestDeleteUserByUsername:
    """Tests for DELETE /user/{username} endpoint."""

    # 1. [Positive] 200 OK with a perfect, complete payload.
    # For DELETE, "perfect, complete payload" refers to the URL and successful operation.
    def test_delete_user_positive_success(self, setup_user, api_key_header):
        """
        Tests deleting an existing user with a valid username.
        Verifies the deletion by attempting to fetch the user afterwards.
        """
        username, _ = setup_user # User is created by fixture
        
        url = f"{BASE_URL}/user/{username}"
        headers = api_key_header

        response = requests.delete(url, headers=headers)
        
        # OpenAPI spec does not explicitly list 200 for DELETE, only 400/404.
        # A successful DELETE typically returns 200 OK or 204 No Content.
        # Petstore's implementation generally returns 200 OK.
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
        
        # Verify deletion by trying to fetch the user
        get_response = requests.get(url)
        assert get_response.status_code == 404, \
            f"Expected 404 Not Found after successful deletion, got {get_response.status_code}. Response: {get_response.text}"

    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    # Part 1: Non-existent user for delete -> 404
    def test_delete_user_negative_not_found(self, api_key_header):
        """Tests deleting a non-existent user, expecting a 404 Not Found."""
        non_existent_username = "non_existent_user_to_delete_" + uuid.uuid4().hex[:8]
        url = f"{BASE_URL}/user/{non_existent_username}"
        headers = api_key_header

        response = requests.delete(url, headers=headers)

        assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}. Response: {response.text}"
        
    # Part 2: Invalid username format in path parameter -> 400/404
    @pytest.mark.parametrize("invalid_username_path", [
        "",  # Empty string
        "   ", # Whitespace string
        "!@#$%^&*()", # Special characters
        "a" * 256 # Extremely long name
    ])
    def test_delete_user_negative_invalid_username_format(self, api_key_header, invalid_username_path):
        """
        Tests deleting with invalid username formats in the path parameter.
        Expects 400 (Invalid username supplied) or 404 (User not found).
        """
        url = f"{BASE_URL}/user/{invalid_username_path}"
        headers = api_key_header

        response = requests.delete(url, headers=headers)
        
        assert response.status_code in [400, 404], \
            f"Expected 400 or 404 for username '{invalid_username_path}', got {response.status_code}. Response: {response.text}"

    # 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    def test_delete_user_security_unauthorized_missing_header(self, setup_user):
        """
        Tests deleting a user without authentication headers, expecting 401 Unauthorized or 403 Forbidden.
        The spec states: "This can only be done by the logged in user."
        """
        username, _ = setup_user
        
        url = f"{BASE_URL}/user/{username}"
        # No API key/Authorization header

        response = requests.delete(url)
        
        assert response.status_code in [401, 403], \
            f"Expected 401 or 403 for unauthorized DELETE, got {response.status_code}. Response: {response.text}"

    def test_delete_user_security_unauthorized_invalid_header(self, setup_user):
        """
        Tests deleting a user with an invalid authentication header, expecting 401 Unauthorized or 403 Forbidden.
        """
        username, _ = setup_user
        
        url = f"{BASE_URL}/user/{username}"
        invalid_headers = {"Authorization": "Bearer another-invalid-jwt"}

        response = requests.delete(url, headers=invalid_headers)
        
        assert response.status_code in [401, 403], \
            f"Expected 401 or 403 for invalid auth DELETE, got {response.status_code}. Response: {response.text}"