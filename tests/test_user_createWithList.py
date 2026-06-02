import pytest
import requests
import uuid
import json

BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = f"{BASE_URL}/user/createWithList"
HEADERS = {'Content-Type': 'application/json'}

def _create_user_payload(user_id_prefix, unique_suffix):
    """
    Helper function to generate a valid user payload with unique identifiers.
    """
    unique_username = f"testuser_{user_id_prefix}_{unique_suffix}"
    return {
        "id": int(f"{user_id_prefix}{unique_suffix[:4]}"), # Ensure ID is an integer
        "username": unique_username,
        "firstName": "John",
        "lastName": "Doe",
        "email": f"{unique_username}@example.com",
        "password": "password123",
        "phone": "123-456-7890",
        "userStatus": 1
    }

# 1. [Positive] 200 OK with a perfect, complete payload.
def test_create_users_with_list_positive_200_ok_complete_payload():
    """
    Test case: Verify successful creation of multiple users with a perfectly
    formed and complete list of user objects in the payload.
    Expected: HTTP 200 OK, with a standard Petstore success message.
    """
    unique_id_1 = uuid.uuid4().hex[:8]
    unique_id_2 = uuid.uuid4().hex[:8]

    user1 = _create_user_payload(1001, unique_id_1)
    user2 = _create_user_payload(1002, unique_id_2)
    payload = [user1, user2]

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    assert response.status_code == 200, \
        f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    
    response_json = response.json()
    assert "code" in response_json and response_json["code"] == 200, \
        f"Expected response code 200, but got {response_json.get('code')}. Response: {response.text}"
    assert "type" in response_json and response_json["type"] == "unknown", \
        f"Expected response type 'unknown', but got {response_json.get('type')}. Response: {response.text}"
    assert "message" in response_json and response_json["message"] == "ok", \
        f"Expected response message 'ok', but got {response_json.get('message')}. Response: {response.text}"

# 2. [Negative] 400/405 Invalid input (missing required fields).
def test_create_users_with_list_negative_missing_username_field():
    """
    Test case: Send a user object missing a critical field like 'username'.
    Expected: Ideally 400 Bad Request. Due to Petstore's leniency, it might
    still return 200 OK, but a robust API should validate schema.
    """
    unique_id = uuid.uuid4().hex[:8]
    user_missing_username = {
        "id": int(f"2001{unique_id[:4]}"),
        "firstName": "Jane",
        "lastName": "Smith",
        "email": f"jane.smith_{unique_id}@example.com",
        "password": "password456",
        "phone": "098-765-4321",
        "userStatus": 1
    }
    payload = [user_missing_username]

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    # Petstore often returns 200 OK even for incomplete user objects
    assert response.status_code == 200, \
        f"Expected status code 200 (due to Petstore leniency), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message, but got {response.text}"

def test_create_users_with_list_negative_empty_list_payload():
    """
    Test case: Send an empty list as the payload. The body is required
    to be an array of User objects, but an empty array technically fulfills this.
    Expected: Ideally 400 Bad Request if no users are considered invalid input.
    Petstore often returns 200 OK.
    """
    payload = []

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    assert response.status_code == 200, \
        f"Expected status code 200 (due to Petstore leniency), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message, but got {response.text}"

# 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
def test_create_users_with_list_negative_username_as_integer():
    """
    Test case: Send a user object where 'username' is an integer instead of a string.
    Expected: Ideally 400 Bad Request for data type mismatch. Petstore might
    attempt type coercion or still return 200 OK.
    """
    unique_id = uuid.uuid4().hex[:8]
    user_with_invalid_username_type = {
        "id": int(f"3001{unique_id[:4]}"),
        "username": 12345,  # Invalid type: integer instead of string
        "firstName": "Charlie",
        "lastName": "Brown",
        "email": f"charlie.brown_{unique_id}@example.com",
        "password": "password789",
        "phone": "111-222-3333",
        "userStatus": 1
    }
    payload = [user_with_invalid_username_type]

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    # Petstore often converts types or is lenient, returning 200 OK.
    assert response.status_code == 200, \
        f"Expected status code 200 (due to Petstore leniency), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message, but got {response.text}"

def test_create_users_with_list_negative_username_as_empty_string():
    """
    Test case: Send a user object with an empty string for the 'username' field.
    Expected: Ideally 400 Bad Request if username requires non-empty string.
    Petstore typically accepts empty strings.
    """
    unique_id = uuid.uuid4().hex[:8]
    user_with_empty_username = _create_user_payload(3002, unique_id)
    user_with_empty_username["username"] = ""  # Empty string for username
    payload = [user_with_empty_username]

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    assert response.status_code == 200, \
        f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message, but got {response.text}"

def test_create_users_with_list_negative_non_list_payload():
    """
    Test case: Send a single user object directly, not wrapped in a list,
    when the schema explicitly expects an array of User objects.
    Expected: Ideally 400 Bad Request for schema violation. Petstore is often
    lenient and might process it as a list of one.
    """
    unique_id = uuid.uuid4().hex[:8]
    single_user_payload = _create_user_payload(4001, unique_id)

    response = requests.post(ENDPOINT, headers=HEADERS, json=single_user_payload)

    # Petstore's /user/createWithList is lenient and accepts a single user object
    # as if it were a list of one, returning 200 OK.
    assert response.status_code == 200, \
        f"Expected status code 200 (due to Petstore leniency), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message, but got {response.text}"

def test_create_users_with_list_negative_null_payload():
    """
    Test case: Send a null payload. The request body is required and must be an array.
    Expected: 400 Bad Request.
    """
    payload = None

    response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

    assert response.status_code == 400, \
        f"Expected status code 400, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "bad input" in response_json["message"].lower(), \
        f"Expected 'bad input' message, but got {response.text}"

# 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
def test_create_users_with_list_security_missing_authorization_header():
    """
    Test case: Simulate an unauthorized request by omitting any Authorization header.
    Note: The Petstore /user/createWithList endpoint is generally unprotected.
    Therefore, it is expected to return 200 OK, even without an Authorization header.
    In a truly protected API, this would typically result in a 401 Unauthorized or 403 Forbidden.
    """
    unique_id = uuid.uuid4().hex[:8]
    user_no_auth = _create_user_payload(5001, unique_id)
    payload = [user_no_auth]

    headers_without_auth = {'Content-Type': 'application/json'}
    response = requests.post(ENDPOINT, headers=headers_without_auth, json=payload)

    assert response.status_code == 200, \
        f"Expected status code 200 (Petstore unprotected), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message for unprotected endpoint, but got {response.text}"

def test_create_users_with_list_security_invalid_authorization_header():
    """
    Test case: Simulate an unauthorized request by providing an invalid Authorization header.
    Note: The Petstore /user/createWithList endpoint is generally unprotected.
    Therefore, it is expected to return 200 OK, even with an invalid Authorization header.
    In a truly protected API, this would typically result in a 401 Unauthorized or 403 Forbidden.
    """
    unique_id = uuid.uuid4().hex[:8]
    user_invalid_auth = _create_user_payload(5002, unique_id)
    payload = [user_invalid_auth]

    headers_invalid_auth = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer a_very_invalid_and_expired_token_12345'
    }
    response = requests.post(ENDPOINT, headers=headers_invalid_auth, json=payload)

    assert response.status_code == 200, \
        f"Expected status code 200 (Petstore unprotected), but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert "message" in response_json and "ok" in response_json["message"], \
        f"Expected success message for unprotected endpoint, but got {response.text}"