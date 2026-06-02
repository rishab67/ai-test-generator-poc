import pytest
import requests
import json
from urllib.parse import urlencode

# Base URL for the Petstore API
BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = "/pet/findByStatus"

# Define a fixture for the base URL to make tests cleaner
@pytest.fixture(scope="module")
def api_base_url():
    return BASE_URL

# Helper function to validate basic Pet structure (assuming common properties)
def validate_pet_structure(pet_data):
    assert isinstance(pet_data, dict)
    assert "id" in pet_data and isinstance(pet_data["id"], (int, float)) # ID can sometimes be float for legacy reasons
    assert "name" in pet_data and isinstance(pet_data["name"], str)
    assert "status" in pet_data and isinstance(pet_data["status"], str)
    assert pet_data["status"] in ["available", "pending", "sold"]

# --- Test Cases ---

# 1. [Positive] 200 OK with a perfect, complete payload.
@pytest.mark.parametrize("status_param", [
    ("available",),
    ("pending",),
    ("sold",),
    ("available", "pending"), # Test with multiple statuses
    ("available", "sold", "pending") # Test with all statuses
])
def test_find_pets_by_status_positive_200_ok(api_base_url, status_param):
    """
    Test finding pets by a valid status (or multiple statuses) successfully.
    Verifies 200 OK and the structure of returned pet objects.
    """
    url = f"{api_base_url}{ENDPOINT}"
    
    # OpenAPI schema specifies 'collectionFormat: multi' for query array,
    # meaning 'status=available&status=pending'
    params = urlencode([("status", s) for s in status_param], doseq=True)
    full_url = f"{url}?{params}"

    response = requests.get(full_url)

    assert response.status_code == 200, \
        f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    
    response_data = response.json()
    assert isinstance(response_data, list), "Response data should be a list of pets."

    if response_data: # If pets are returned, validate their structure
        for pet in response_data:
            validate_pet_structure(pet)
            # Ensure the returned pet's status is one of the requested statuses
            assert pet["status"] in status_param, \
                f"Pet with status '{pet['status']}' found, but only '{status_param}' were requested."
    else:
        # It's okay to get an empty list if no pets match the status
        pass

# 2. [Negative] 400 Invalid input (missing required fields).
def test_find_pets_by_status_negative_400_missing_status(api_base_url):
    """
    Test sending a request without the required 'status' query parameter.
    Expects a 400 Bad Request error.
    """
    url = f"{api_base_url}{ENDPOINT}"
    
    # Do not provide the 'status' parameter
    response = requests.get(url)

    assert response.status_code == 400, \
        f"Expected status code 400 for missing 'status' parameter, but got {response.status_code}. Response: {response.text}"
    assert "Invalid status value" in response.text or "message" in response.json(), \
        "Response message should indicate invalid/missing status."

# 3. [Negative] 400 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
@pytest.mark.parametrize("invalid_status_param", [
    ("invalid_status_string",),
    ("123",), # Integer as string, but not in enum
    ("AVAILABLE",), # Case sensitivity (enum is lowercase)
    ("",), # Empty string
    ("available", "invalid_status"), # Mixed valid and invalid
    ("available", ""), # Mixed valid and empty
    (None,), # None, though requests usually converts to 'None' string
])
def test_find_pets_by_status_negative_400_invalid_status_values(api_base_url, invalid_status_param):
    """
    Test finding pets by an invalid or non-enum status value.
    Expects a 400 Bad Request error.
    """
    url = f"{api_base_url}{ENDPOINT}"
    
    # OpenAPI schema specifies 'collectionFormat: multi' for query array,
    # meaning 'status=invalid_status_string' or 'status=available&status=invalid_status'
    params = urlencode([("status", str(s)) for s in invalid_status_param if s is not None], doseq=True)
    
    # Handle the case where invalid_status_param is (None,) leading to empty params
    if not params:
        full_url = url # Simulates missing parameter which is handled by a different test
        response = requests.get(full_url)
        assert response.status_code == 400, \
            f"Expected 400 for invalid/missing status, got {response.status_code} for {invalid_status_param}. Response: {response.text}"
    else:
        full_url = f"{url}?{params}"
        response = requests.get(full_url)

        assert response.status_code == 400, \
            f"Expected status code 400 for invalid status '{invalid_status_param}', but got {response.status_code}. Response: {response.text}"
        assert "Invalid status value" in response.text or "message" in response.json(), \
            "Response message should indicate invalid status."


# 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
def test_find_pets_by_status_security_unauthorized(api_base_url):
    """
    Test accessing the endpoint without authentication headers, as the schema
    specifies 'petstore_auth' security.
    Expects 401 Unauthorized or 403 Forbidden, indicating security enforcement.
    Note: The public Petstore API often allows unauthenticated read access,
    which would be a finding if a 401/403 is expected based on schema.
    For this test, we assert the *desired secure* behavior.
    """
    url = f"{api_base_url}{ENDPOINT}?status=available"
    
    # Simulate missing authentication by not providing any Authorization header
    headers = {} 
    
    response = requests.get(url, headers=headers)

    # The actual Petstore API public instance *does* allow unauthenticated access for GET /findByStatus.
    # Therefore, asserting 401/403 will likely fail against the public API.
    # As a security tester, I would document this as a finding:
    # "Endpoint /pet/findByStatus, despite declaring 'petstore_auth' security with 'read:pets' scope,
    # allows unauthenticated access (returns 200 OK)."
    # However, to strictly adhere to the prompt's implied security expectation (401/403),
    # I will assert for 401 or 403.
    # If this test runs against a real API, the discrepancy indicates a security testing finding.

    assert response.status_code in [401, 403], \
        f"Expected status code 401 or 403 for unauthorized access, but got {response.status_code}. " \
        f"This might indicate that the API allows unauthenticated access despite security requirements. Response: {response.text}"
    
    if response.status_code == 401:
        assert "Unauthorized" in response.text or "message" in response.json(), \
            "Response message should indicate unauthorized access."
    elif response.status_code == 403:
        assert "Forbidden" in response.text or "message" in response.json(), \
            "Response message should indicate forbidden access."

def test_find_pets_by_status_security_invalid_token(api_base_url):
    """
    Test accessing the endpoint with an invalid authentication token.
    Expects 401 Unauthorized or 403 Forbidden.
    """
    url = f"{api_base_url}{ENDPOINT}?status=available"
    
    # Simulate an invalid authentication token
    invalid_token = "Bearer invalid_jwt_token_12345"
    headers = {"Authorization": invalid_token}
    
    response = requests.get(url, headers=headers)

    assert response.status_code in [401, 403], \
        f"Expected status code 401 or 403 for invalid token, but got {response.status_code}. " \
        f"This might indicate weak security validation. Response: {response.text}"
    
    if response.status_code == 401:
        assert "Unauthorized" in response.text or "message" in response.json(), \
            "Response message should indicate unauthorized access for invalid token."
    elif response.status_code == 403:
        assert "Forbidden" in response.text or "message" in response.json(), \
            "Response message should indicate forbidden access for invalid token."