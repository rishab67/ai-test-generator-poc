import pytest
import requests
import json

BASE_URL = "https://petstore.swagger.io/v2"

# Define a fixture for creating a sample user payload
@pytest.fixture
def sample_user_payload():
    return [
        {
            "id": 101,
            "username": "testuser1",
            "firstName": "Test",
            "lastName": "User1",
            "email": "testuser1@example.com",
            "password": "password123",
            "phone": "123-456-7890",
            "userStatus": 1
        },
        {
            "id": 102,
            "username": "testuser2",
            "firstName": "Another",
            "lastName": "User2",
            "email": "testuser2@example.com",
            "password": "securepassword",
            "phone": "098-765-4321",
            "userStatus": 0
        }
    ]

def test_create_users_with_list_success(sample_user_payload):
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}

    response = requests.post(endpoint, data=json.dumps(sample_user_payload), headers=headers)

    assert response.status_code == 200
    # The API documentation for this endpoint indicates a 'default' response,
    # which typically means a 200 OK with a generic success message or no content.
    # We can add checks for specific content if the API contract was more detailed.

def test_create_users_with_list_empty_payload():
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}
    empty_payload = []

    response = requests.post(endpoint, data=json.dumps(empty_payload), headers=headers)

    # Based on typical API behavior, an empty list might result in a 200 OK
    # with a success indication, or potentially a 400 Bad Request if it's considered invalid input.
    # Assuming 200 OK for this test case.
    assert response.status_code == 200

def test_create_users_with_list_invalid_payload_structure():
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}
    invalid_payload = [
        {"invalid_field": "value"}
    ]

    response = requests.post(endpoint, data=json.dumps(invalid_payload), headers=headers)

    # An invalid payload structure should ideally result in a client error (4xx).
    # We'll expect a 400 or 422. If the API defaults to 200 for malformed data,
    # this test would need adjustment or the API itself would be considered flawed.
    assert response.status_code in [400, 422]

def test_create_users_with_list_missing_required_field():
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}
    payload_missing_username = [
        {
            "id": 103,
            "firstName": "Missing",
            "lastName": "Username",
            "email": "nousername@example.com",
            "password": "password",
            "phone": "555-1212",
            "userStatus": 1
        }
    ]

    response = requests.post(endpoint, data=json.dumps(payload_missing_username), headers=headers)

    # Missing required fields should result in a client error.
    assert response.status_code in [400, 422]

def test_create_users_with_list_duplicate_user_id():
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}
    payload_duplicate_id = [
        {
            "id": 104,
            "username": "dupuser1",
            "firstName": "Dup",
            "lastName": "User1",
            "email": "dupuser1@example.com",
            "password": "password",
            "phone": "111-222-3333",
            "userStatus": 1
        },
        {
            "id": 104,  # Duplicate ID
            "username": "dupuser2",
            "firstName": "Dup",
            "lastName": "User2",
            "email": "dupuser2@example.com",
            "password": "password",
            "phone": "444-555-6666",
            "userStatus": 1
        }
    ]

    response = requests.post(endpoint, data=json.dumps(payload_duplicate_id), headers=headers)

    # Handling of duplicate IDs can vary. It might succeed if the API
    # ignores duplicates, or fail if it's a strict constraint.
    # Assuming it might result in an error for the duplicate.
    assert response.status_code in [200, 400, 409] # 409 Conflict is common for duplicates

def test_create_users_with_list_invalid_email_format():
    endpoint = f"{BASE_URL}/user/createWithList"
    headers = {"Content-Type": "application/json"}
    payload_invalid_email = [
        {
            "id": 105,
            "username": "bademailuser",
            "firstName": "Bad",
            "lastName": "Email",
            "email": "invalid-email-format",  # Invalid email
            "password": "password",
            "phone": "777-888-9999",
            "userStatus": 1
        }
    ]

    response = requests.post(endpoint, data=json.dumps(payload_invalid_email), headers=headers)

    # Invalid data formats should generally result in a client error.
    assert response.status_code in [400, 422]