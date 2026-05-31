import pytest
import requests
from typing import Dict, Any

BASE_URL = "https://petstore.swagger.io/v2"
API_KEY = "special-key"  # Example API key, assuming some authentication mechanism

def test_upload_image_positive_200_ok():
    """
    [Positive] Test case for uploading an image with a valid pet ID and file.
    """
    # First, create a pet to get a valid petId
    pet_data = {
        "category": {"id": 1, "name": "Dogs"},
        "name": "Buddy",
        "photoUrls": ["http://example.com/buddy.jpg"],
        "tags": [{"id": 1, "name": "cute"}],
        "status": "available"
    }
    create_pet_response = requests.post(f"{BASE_URL}/pet", json=pet_data)
    assert create_pet_response.status_code == 200
    pet_id = create_pet_response.json().get("id")
    assert pet_id is not None

    # Prepare the image file
    image_file_path = "test_image.jpg"  # Replace with a path to a real image file
    try:
        with open(image_file_path, "wb") as f:
            f.write(b"This is a dummy image file content.")
    except IOError:
        pytest.skip(f"Could not create dummy image file at {image_file_path}. Skipping test.")

    files = {'file': (image_file_path, open(image_file_path, 'rb'), 'image/jpeg')}
    data = {'additionalMetadata': 'This is a test image'}

    headers = {
        "api_key": API_KEY
    }

    response = requests.post(
        f"{BASE_URL}/pet/{pet_id}/uploadImage",
        files=files,
        data=data,
        headers=headers
    )

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "code" in response_data
    assert "type" in response_data
    assert "message" in response_data
    assert response_data["code"] == 200
    assert response_data["type"] == "unknown"  # Or whatever the expected type is for success

    # Clean up the created pet
    delete_response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=headers)
    assert delete_response.status_code == 200

def test_upload_image_negative_invalid_input_missing_fields():
    """
    [Negative] Test case for invalid input, specifically missing required fields (petId).
    """
    # Intentionally not providing a petId in the URL, which is a required path parameter
    files = {'file': ('test_image.jpg', b'dummy content', 'image/jpeg')}
    data = {'additionalMetadata': 'This is a test image'}

    headers = {
        "api_key": API_KEY
    }

    response = requests.post(
        f"{BASE_URL}/pet/uploadImage",  # Missing petId
        files=files,
        data=data,
        headers=headers
    )

    # The API might return 404 if the route is not found, or 400/405 if path parameter is missing.
    # Based on Swagger, the path parameter is required, so a missing one should be a client error.
    assert response.status_code in [400, 404, 405]

def test_upload_image_negative_boundary_testing_invalid_types():
    """
    [Negative] Test case for boundary testing with invalid data types.
    """
    # First, create a pet to get a valid petId
    pet_data = {
        "category": {"id": 1, "name": "Dogs"},
        "name": "Buddy",
        "photoUrls": ["http://example.com/buddy.jpg"],
        "tags": [{"id": 1, "name": "cute"}],
        "status": "available"
    }
    create_pet_response = requests.post(f"{BASE_URL}/pet", json=pet_data)
    assert create_pet_response.status_code == 200
    pet_id = create_pet_response.json().get("id")
    assert pet_id is not None

    # Test with invalid type for petId (string instead of integer)
    files = {'file': ('test_image.jpg', b'dummy content', 'image/jpeg')}
    data = {'additionalMetadata': 'This is a test image'}
    headers = {
        "api_key": API_KEY
    }

    response_invalid_pet_id = requests.post(
        f"{BASE_URL}/pet/invalid_id/uploadImage",
        files=files,
        data=data,
        headers=headers
    )
    assert response_invalid_pet_id.status_code in [400, 405]

    # Test with invalid type for additionalMetadata (integer instead of string)
    files = {'file': ('test_image.jpg', b'dummy content', 'image/jpeg')}
    data_invalid_metadata = {'additionalMetadata': 12345}
    headers = {
        "api_key": API_KEY
    }

    response_invalid_metadata = requests.post(
        f"{BASE_URL}/pet/{pet_id}/uploadImage",
        files=files,
        data=data_invalid_metadata,
        headers=headers
    )
    assert response_invalid_metadata.status_code in [400, 405]

    # Test with empty string for additionalMetadata (should be valid but can be tested)
    files = {'file': ('test_image.jpg', b'dummy content', 'image/jpeg')}
    data_empty_metadata = {'additionalMetadata': ''}
    headers = {
        "api_key": API_KEY
    }

    response_empty_metadata = requests.post(
        f"{BASE_URL}/pet/{pet_id}/uploadImage",
        files=files,
        data=data_empty_metadata,
        headers=headers
    )
    assert response_empty_metadata.status_code == 200 # Assuming empty string is valid

    # Clean up the created pet
    delete_response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=headers)
    assert delete_response.status_code == 200


def test_upload_image_security_unauthorized_missing_auth():
    """
    [Security] Test case for unauthorized access by missing authentication headers.
    """
    # First, create a pet to get a valid petId
    pet_data = {
        "category": {"id": 1, "name": "Dogs"},
        "name": "Buddy",
        "photoUrls": ["http://example.com/buddy.jpg"],
        "tags": [{"id": 1, "name": "cute"}],
        "status": "available"
    }
    create_pet_response = requests.post(f"{BASE_URL}/pet", json=pet_data)
    assert create_pet_response.status_code == 200
    pet_id = create_pet_response.json().get("id")
    assert pet_id is not None

    # Prepare the image file
    image_file_path = "test_image.jpg"
    try:
        with open(image_file_path, "wb") as f:
            f.write(b"This is a dummy image file content.")
    except IOError:
        pytest.skip(f"Could not create dummy image file at {image_file_path}. Skipping test.")

    files = {'file': (image_file_path, open(image_file_path, 'rb'), 'image/jpeg')}
    data = {'additionalMetadata': 'This is a test image'}

    # Missing "api_key" header
    response = requests.post(
        f"{BASE_URL}/pet/{pet_id}/uploadImage",
        files=files,
        data=data,
        headers={}  # Empty headers
    )

    # The expected behavior for missing authentication in Petstore is often 401 or 403
    assert response.status_code in [401, 403]

    # Clean up the created pet (if the unauthorized request didn't create it implicitly)
    # Attempt cleanup with a valid key just in case
    headers_for_cleanup = {
        "api_key": API_KEY
    }
    delete_response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=headers_for_cleanup)
    assert delete_response.status_code == 200

def test_upload_image_security_unauthorized_invalid_auth():
    """
    [Security] Test case for unauthorized access by providing an invalid authentication token.
    """
    # First, create a pet to get a valid petId
    pet_data = {
        "category": {"id": 1, "name": "Dogs"},
        "name": "Buddy",
        "photoUrls": ["http://example.com/buddy.jpg"],
        "tags": [{"id": 1, "name": "cute"}],
        "status": "available"
    }
    create_pet_response = requests.post(f"{BASE_URL}/pet", json=pet_data)
    assert create_pet_response.status_code == 200
    pet_id = create_pet_response.json().get("id")
    assert pet_id is not None

    # Prepare the image file
    image_file_path = "test_image.jpg"
    try:
        with open(image_file_path, "wb") as f:
            f.write(b"This is a dummy image file content.")
    except IOError:
        pytest.skip(f"Could not create dummy image file at {image_file_path}. Skipping test.")

    files = {'file': (image_file_path, open(image_file_path, 'rb'), 'image/jpeg')}
    data = {'additionalMetadata': 'This is a test image'}

    # Providing an invalid API key
    headers = {
        "api_key": "invalid-api-key"
    }

    response = requests.post(
        f"{BASE_URL}/pet/{pet_id}/uploadImage",
        files=files,
        data=data,
        headers=headers
    )

    # The expected behavior for invalid authentication in Petstore is often 401 or 403
    assert response.status_code in [401, 403]

    # Clean up the created pet (if the unauthorized request didn't create it implicitly)
    # Attempt cleanup with a valid key just in case
    headers_for_cleanup = {
        "api_key": API_KEY
    }
    delete_response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=headers_for_cleanup)
    assert delete_response.status_code == 200