import pytest
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

BASE_URL = "https://petstore.swagger.io/v2"

# Helper function to create a pet for testing purposes
def create_pet(pet_data):
    try:
        response = requests.post(f"{BASE_URL}/pet", json=pet_data, timeout=10)
        response.raise_for_status()
        return response.json()
    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Failed to create pet: {e}")
        return None

# Helper function to delete a pet
def delete_pet(pet_id):
    try:
        response = requests.delete(f"{BASE_URL}/pet/{pet_id}", timeout=10)
        if response.status_code not in [200, 404]: # Allow 404 if pet doesn't exist
            response.raise_for_status()
    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Failed to delete pet: {e}")

# Define a fixture for a sample pet
@pytest.fixture(scope="module")
def sample_pet():
    pet_data = {
        "id": 123456789,
        "name": "Buddy",
        "category": {"id": 1, "name": "Dogs"},
        "photoUrls": ["string"],
        "tags": [{"id": 1, "name": "friendly"}],
        "status": "available"
    }
    created_pet = create_pet(pet_data)
    if created_pet:
        yield created_pet
        delete_pet(created_pet.get("id"))
    else:
        pytest.skip("Could not create a sample pet for testing.")

# 1. [Positive] 200 OK with a perfect, complete payload.
def test_find_pets_by_status_positive_perfect_payload(sample_pet):
    if not sample_pet:
        pytest.skip("Skipping test due to sample_pet fixture failure.")

    status_to_find = sample_pet.get("status", "available")
    params = {'status': status_to_find}
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        assert response.status_code == 200
        response_json = response.json()
        assert isinstance(response_json, list)
        # Check if the created pet is in the response
        found_pet = any(pet.get("id") == sample_pet.get("id") for pet in response_json)
        assert found_pet, f"Sample pet with ID {sample_pet.get('id')} not found in the results for status '{status_to_find}'"
        # Further assertions on the structure of pets in the response if needed
        if response_json:
            assert isinstance(response_json[0], dict)
            assert "id" in response_json[0]
            assert "name" in response_json[0]
            assert "status" in response_json[0]

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

# 2. [Negative] 400/405 Invalid input (missing required fields).
# The 'status' parameter is marked as 'required': True in the schema.
def test_find_pets_by_status_negative_missing_required_field():
    params = {}  # Missing the required 'status' parameter
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        # According to the schema, invalid status should result in 400.
        # However, missing a required query parameter can sometimes lead to 405 or other errors depending on server implementation.
        # We'll assert for a client error code indicating invalid request.
        assert response.status_code in [400, 405], f"Expected 400 or 405, but got {response.status_code}"
        assert "Invalid status value" in response.text or "Missing required parameter" in response.text

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")

# 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
def test_find_pets_by_status_negative_invalid_status_type():
    params = {'status': 123}  # Sending an integer instead of a string
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        assert response.status_code == 400, f"Expected 400, but got {response.status_code}"
        assert "Invalid status value" in response.text

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

def test_find_pets_by_status_negative_invalid_status_enum_value():
    params = {'status': 'nonexistent'}  # Sending a status not in the enum
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        assert response.status_code == 400, f"Expected 400, but got {response.status_code}"
        assert "Invalid status value" in response.text

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

def test_find_pets_by_status_negative_empty_status_string():
    params = {'status': ''}  # Sending an empty string for status
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        # An empty string is not a valid enum value.
        assert response.status_code == 400, f"Expected 400, but got {response.status_code}"
        assert "Invalid status value" in response.text

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

def test_find_pets_by_status_negative_multiple_invalid_statuses():
    params = {'status': ['available', 'invalid_status', 'pending']}  # One invalid status in a list
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        # If one of the statuses is invalid, the entire request might be considered invalid.
        assert response.status_code == 400, f"Expected 400, but got {response.status_code}"
        assert "Invalid status value" in response.text

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

# 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
# The schema indicates 'petstore_auth' with 'write:pets', 'read:pets' scopes.
# For a GET request like findPetsByStatus, 'read:pets' is usually sufficient.
# We will simulate missing authentication.
def test_find_pets_by_status_security_unauthorized_no_auth():
    params = {'status': 'available'}
    # No authorization header provided

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, timeout=10)
        # For secured endpoints without auth, typically 401 Unauthorized is returned.
        assert response.status_code == 401, f"Expected 401, but got {response.status_code}"

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")

# Note: To test invalid/expired tokens (403), you would need to obtain a valid token
# and then either expire it or use a token with insufficient scopes.
# This is more complex to automate without an actual auth server setup.
# The test below simulates an invalid token format, which might result in 401 or 403 depending on implementation.
def test_find_pets_by_status_security_unauthorized_invalid_token():
    params = {'status': 'available'}
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer invalid_token_format'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        # Depending on the server's authentication middleware, this could be 401 or 403.
        # We'll assert for a client error code.
        assert response.status_code in [401, 403], f"Expected 401 or 403, but got {response.status_code}"

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")

# Test with multiple statuses
def test_find_pets_by_status_multiple_valid_statuses():
    # To make this test reliable, we'd ideally create pets with different statuses.
    # For simplicity, we'll just test with valid enum values.
    params = {'status': ['available', 'pending']}
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        assert response.status_code == 200
        response_json = response.json()
        assert isinstance(response_json, list)
        if response_json:
            # Check if all returned pets have a status that is either 'available' or 'pending'
            for pet in response_json:
                assert pet.get("status") in ['available', 'pending'], f"Found pet with unexpected status: {pet.get('status')}"

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")
    except ValueError:
        pytest.fail("Response is not valid JSON.")

# Test with Accept header for XML (as per schema 'produces': ['application/json', 'application/xml'])
def test_find_pets_by_status_accept_xml():
    params = {'status': 'available'}
    headers = {'Accept': 'application/xml'}

    try:
        response = requests.get(f"{BASE_URL}/pet/findByStatus", params=params, headers=headers, timeout=10)
        assert response.status_code == 200
        assert 'application/xml' in response.headers.get('Content-Type', '')
        # Asserting the XML structure is more complex and might involve libraries like xmltodict or lxml.
        # For now, we'll just check if it looks like XML and contains a common element.
        assert response.text.strip().startswith('<')
        assert '<Pet>' in response.text or '<pet>' in response.text # Example tag, adjust if schema defines differently

    except (ConnectionError, Timeout, RequestException) as e:
        pytest.fail(f"Request failed: {e}")