import pytest
import requests
import os
import json

BASE_URL = "https://petstore.swagger.io/v2"

# --- Fixtures for Setup and Teardown ---

@pytest.fixture(scope="module")
def api_key_header():
    """
    Provides a valid API key header for authentication.
    For the Petstore API, a common pattern for 'petstore_auth' is to use
    an 'api_key' in the header. The exact value might vary, but for demo,
    'special-key' or any non-empty string often works.
    """
    return {"api_key": "special-key"}

@pytest.fixture(scope="module")
def invalid_api_key_header():
    """Provides an invalid API key header for security tests."""
    return {"api_key": "invalid-security-token-12345"}

@pytest.fixture(scope="module")
def pet_id(api_key_header):
    """
    Fixture to create a pet before tests run and delete it afterwards.
    This ensures a valid and dynamic petId for the uploadImage tests.
    Returns the created pet's ID.
    """
    # 1. Create a pet
    create_pet_url = f"{BASE_URL}/pet"
    pet_payload = {
        "id": 0,  # The API will typically assign a new ID if 0 or omitted
        "category": {"id": 1, "name": "dogs"},
        "name": "doggie_for_upload_test",
        "photoUrls": ["http://example.com/photo.jpg"],
        "tags": [{"id": 10, "name": "test-tag"}],
        "status": "available"
    }

    # Pet creation endpoint expects application/json
    headers = {"Content-Type": "application/json"}
    headers.update(api_key_header)  # Add API key for creation

    print(f"\nAttempting to create pet for test: {create_pet_url}")
    response = requests.post(create_pet_url, headers=headers, json=pet_payload)
    assert response.status_code == 200, f"Failed to create pet. Status: {response.status_code}, Response: {response.text}"
    
    created_pet_id = response.json()['id']
    print(f"Successfully created pet with ID: {created_pet_id}")

    yield created_pet_id  # Provide the pet ID to the tests

    # 2. Delete the pet after tests complete
    delete_pet_url = f"{BASE_URL}/pet/{created_pet_id}"
    delete_headers = api_key_header  # Use the same API key for deletion

    print(f"Attempting to delete pet after tests: {delete_pet_url}")
    delete_response = requests.delete(delete_pet_url, headers=delete_headers)
    assert delete_response.status_code == 200, f"Failed to delete pet {created_pet_id}. Status: {delete_response.status_code}, Response: {delete_response.text}"
    print(f"Successfully deleted pet with ID: {created_pet_id}")


# --- Test Cases ---

def test_upload_image_positive_200_ok(pet_id, api_key_header):
    """
    [Positive] 200 OK with a perfect, complete payload.
    Uploads an image with additional metadata for a valid pet using multipart/form-data.
    """
    endpoint = f"/pet/{pet_id}/uploadImage"
    url = f"{BASE_URL}{endpoint}"

    # Prepare multipart/form-data payload
    additional_metadata = "Comprehensive test photo upload from Pytest script."
    file_content = b"This is a dummy binary image content for testing purposes.\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82"
    file_name = "test_image_full.png"
    file_mimetype = "image/png"

    # `files` parameter in requests automatically sets Content-Type to multipart/form-data
    # and handles file encoding.
    files = {'file': (file_name, file_content, file_mimetype)}
    data = {'additionalMetadata': additional_metadata}

    headers = api_key_header  # Include API key header for authentication

    print(f"\nExecuting positive test for URL: {url}")
    response = requests.post(url, headers=headers, files=files, data=data)

    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "code" in response_json, "Response JSON missing 'code' field."
    assert "type" in response_json, "Response JSON missing 'type' field."
    assert "message" in response_json, "Response JSON missing 'message' field."
    assert response_json["code"] == 200, f"Expected code 200, got {response_json['code']}."
    assert "uploaded" in response_json["message"], "Response message should indicate successful upload."
    assert file_name in response_json["message"], f"Response message should contain uploaded file name '{file_name}'."
    assert additional_metadata in response_json["message"], f"Response message should contain additional metadata '{additional_metadata}'."


def test_upload_image_negative_400_invalid_pet_id_type(api_key_header):
    """
    [Negative] 400/404/405 Invalid input: `petId` type mismatch (string instead of int64).
    Petstore API typically returns 404 Not Found for non-integer path parameters
    when an integer is expected, as the routing fails before handler execution.
    """
    invalid_pet_id = "non-numeric-id"  # Expecting integer (int64), sending string
    endpoint = f"/pet/{invalid_pet_id}/uploadImage"
    url = f"{BASE_URL}{endpoint}"

    files = {'file': ('test.jpg', b'dummy content', 'image/jpeg')}
    data = {'additionalMetadata': 'some metadata'}
    headers = api_key_header

    print(f"\nExecuting negative test (invalid pet ID type) for URL: {url}")
    response = requests.post(url, headers=headers, files=files, data=data)

    # For petstore.swagger.io, a string petId typically results in 404 (Not Found)
    # because the routing regex for {petId} (int) doesn't match.
    # If the router was more forgiving and passed it to the handler, a 400 (Bad Request)
    # would be expected from type validation. 405 (Method Not Allowed) is also possible
    # if the route exists but not for POST, which is less likely here.
    assert response.status_code in [400, 404], \
        f"Expected status code 400 or 404, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "message" in response_json


def test_upload_image_negative_400_empty_metadata_and_file(pet_id, api_key_header):
    """
    [Negative] 200 (boundary testing): Sending empty string for metadata and an empty file.
    The OpenAPI schema marks `additionalMetadata` and `file` as optional.
    Therefore, the API should generally accept empty values and return 200 OK,
    unless specific server-side validation rules are in place for minimum content.
    This test verifies the API's behavior for such boundary conditions.
    """
    endpoint = f"/pet/{pet_id}/uploadImage"
    url = f"{BASE_URL}{endpoint}"

    empty_additional_metadata = ""
    empty_file_content = b""  # An empty file
    empty_file_name = "empty_file.txt"
    empty_file_mimetype = "text/plain"

    files = {'file': (empty_file_name, empty_file_content, empty_file_mimetype)}
    data = {'additionalMetadata': empty_additional_metadata}
    headers = api_key_header

    print(f"\nExecuting boundary test (empty metadata and file) for URL: {url}")
    response = requests.post(url, headers=headers, files=files, data=data)

    # Given that `additionalMetadata` and `file` are optional, 200 OK is expected.
    # The Petstore API handles this gracefully, treating them as valid but empty inputs.
    assert response.status_code == 200, \
        f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert response_json["code"] == 200
    assert "uploaded" in response_json["message"]
    assert empty_file_name in response_json["message"]


def test_upload_image_security_401_missing_authentication(pet_id):
    """
    [Security] 401/403 Unauthorized: Simulate missing authentication headers.
    The endpoint requires 'petstore_auth'. Omitting the required 'api_key'
    header should result in an authorization error.
    """
    endpoint = f"/pet/{pet_id}/uploadImage"
    url = f"{BASE_URL}{endpoint}"

    files = {'file': ('missing_auth.jpg', b'image content', 'image/jpeg')}
    data = {'additionalMetadata': 'metadata without auth'}

    # Intentionally do not send the 'api_key' header
    print(f"\nExecuting security test (missing authentication) for URL: {url}")
    response = requests.post(url, files=files, data=data)

    # Petstore API typically returns 401 Unauthorized when the 'api_key'
    # header is completely absent, indicating authentication is required.
    # 403 Forbidden might be returned if an invalid, but present, auth token
    # is provided, or if the token lacks necessary scopes.
    assert response.status_code in [401, 403], \
        f"Expected status code 401 or 403, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "message" in response_json
    assert any(msg in response_json["message"].lower() for msg in ["unauthorized", "authentication required", "access denied", "invalid token"])


def test_upload_image_security_401_invalid_authentication(pet_id, invalid_api_key_header):
    """
    [Security] 401/403 Unauthorized: Simulate invalid authentication headers.
    Providing an 'api_key' header with an invalid or unrecognized value
    should result in an authorization error.
    """
    endpoint = f"/pet/{pet_id}/uploadImage"
    url = f"{BASE_URL}{endpoint}"

    files = {'file': ('invalid_auth.jpg', b'image content', 'image/jpeg')}
    data = {'additionalMetadata': 'metadata with invalid auth'}

    headers = invalid_api_key_header  # Use the fixture providing an invalid API key

    print(f"\nExecuting security test (invalid authentication) for URL: {url}")
    response = requests.post(url, headers=headers, files=files, data=data)

    # Similar to missing authentication, an invalid key should also result
    # in 401 Unauthorized or 403 Forbidden, depending on server implementation.
    assert response.status_code in [401, 403], \
        f"Expected status code 401 or 403, but got {response.status_code}. Response: {response.text}"
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "message" in response_json
    assert any(msg in response_json["message"].lower() for msg in ["unauthorized", "authentication failed", "invalid key", "access denied", "invalid token"])