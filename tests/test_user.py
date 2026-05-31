import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

# Define a sample user payload based on the expected schema
# Assuming the User schema in OpenAPI has fields like 'id', 'username', 'firstName', 'lastName', 'email', 'password', 'phone', 'userStatus'
SAMPLE_USER_PAYLOAD = {
    "id": 12345,
    "username": "testuser_pytest",
    "firstName": "Test",
    "lastName": "User",
    "email": "test.user@example.com",
    "password": "password123",
    "phone": "123-456-7890",
    "userStatus": 1
}

def test_create_user_success():
    """
    Tests the successful creation of a user.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        json=SAMPLE_USER_PAYLOAD,
        headers=headers
    )
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    # Add more assertions here if the response body contains specific details about the created user
    # For example, if the response returns the created user object:
    # assert response.json()["username"] == SAMPLE_USER_PAYLOAD["username"]

def test_create_user_missing_required_field():
    """
    Tests creating a user with a missing required field (e.g., username).
    """
    invalid_payload = SAMPLE_USER_PAYLOAD.copy()
    del invalid_payload["username"] # Assuming username is a required field

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        json=invalid_payload,
        headers=headers
    )
    # The expected status code for a bad request might vary depending on the API's error handling.
    # Common codes are 400 (Bad Request). Let's assume 400 for this test.
    assert response.status_code == 400, f"Expected status code 400, but got {response.status_code}. Response: {response.text}"

def test_create_user_invalid_data_type():
    """
    Tests creating a user with an invalid data type for a field.
    """
    invalid_payload = SAMPLE_USER_PAYLOAD.copy()
    invalid_payload["id"] = "not_an_integer" # Assuming 'id' should be an integer

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        json=invalid_payload,
        headers=headers
    )
    # Again, the expected status code for invalid data types can vary. Assuming 400.
    assert response.status_code == 400, f"Expected status code 400, but got {response.status_code}. Response: {response.text}"

def test_create_user_duplicate_username():
    """
    Tests creating a user with a username that already exists.
    This assumes the API will reject duplicate usernames.
    First, create a user. Then, try to create another with the same username.
    """
    # Create the first user
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    first_user_payload = {
        "id": 67890,
        "username": "duplicateuser_pytest",
        "firstName": "Dup",
        "lastName": "User",
        "email": "dup.user@example.com",
        "password": "password456",
        "phone": "987-654-3210",
        "userStatus": 0
    }
    response_first = requests.post(
        f"{BASE_URL}/user",
        json=first_user_payload,
        headers=headers
    )
    assert response_first.status_code == 200, f"Failed to create the first user. Status: {response_first.status_code}, Response: {response_first.text}"

    # Attempt to create a second user with the same username
    second_user_payload = first_user_payload.copy()
    second_user_payload["id"] = 11111 # Use a different ID

    response_second = requests.post(
        f"{BASE_URL}/user",
        json=second_user_payload,
        headers=headers
    )
    # Expecting an error code, likely 409 Conflict or 400 Bad Request
    # Assuming 400 for this example, but 409 is also common for duplicate resource creation
    assert response_second.status_code == 400, f"Expected status code 400 for duplicate username, but got {response_second.status_code}. Response: {response_second.text}"

    # Clean up the first user if the API supports deletion, or assume it's managed externally
    # For simplicity in this example, we're not including a delete test or cleanup.

def test_create_user_with_xml_accept_header():
    """
    Tests creating a user and requesting an XML response.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/xml"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        json=SAMPLE_USER_PAYLOAD,
        headers=headers
    )
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    assert response.headers['Content-Type'].startswith('application/xml')
    # Add assertions to check the XML response content if applicable

def test_create_user_with_invalid_content_type():
    """
    Tests creating a user with an invalid Content-Type header.
    """
    headers = {
        "Content-Type": "application/xml", # Incorrect content type for sending JSON
        "Accept": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        json=SAMPLE_USER_PAYLOAD, # Sending JSON data
        headers=headers
    )
    # Typically, an API will return a 415 Unsupported Media Type for an incorrect Content-Type
    assert response.status_code == 415, f"Expected status code 415, but got {response.status_code}. Response: {response.text}"

def test_create_user_without_json_body():
    """
    Tests calling the endpoint without sending a JSON body.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/user",
        headers=headers # No json= argument
    )
    # Missing required body should result in a Bad Request (400)
    assert response.status_code == 400, f"Expected status code 400 for missing body, but got {response.status_code}. Response: {response.text}"