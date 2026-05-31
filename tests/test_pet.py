import pytest
import requests
import json

BASE_URL = "https://petstore.swagger.io/v2"

# --- Helper Functions ---

def create_valid_pet_payload():
    return {
        "id": 9999,
        "category": {
            "id": 1,
            "name": "Dogs"
        },
        "name": "Buddy",
        "photoUrls": [
            "http://example.com/buddy.jpg"
        ],
        "tags": [
            {
                "id": 10,
                "name": "friendly"
            }
        ],
        "status": "available"
    }

def get_pet_schema():
    # In a real scenario, you'd fetch this from the OpenAPI spec.
    # For this example, we'll define a simplified schema structure based on the provided OpenAPI snippet.
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "format": "int64"},
            "category": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"}
                }
            },
            "name": {"type": "string"},
            "photoUrls": {
                "type": "array",
                "items": {"type": "string"}
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "format": "int64"},
                        "name": {"type": "string"}
                    }
                }
            },
            "status": {"type": "string", "enum": ["available", "pending", "sold"]}
        },
        "required": ["name", "photoUrls"]
    }

# --- Fixtures ---

@pytest.fixture
def api_client():
    return requests

@pytest.fixture(scope="module")
def auth_headers():
    # This token is for demonstration purposes and may not work.
    # In a real test, this would be obtained via an OAuth flow or a mock server.
    return {"api_key": "special-key"}

@pytest.fixture(scope="module")
def invalid_auth_headers():
    return {"api_key": "invalid-key"}

@pytest.fixture(scope="module")
def missing_auth_headers():
    return {}

# --- Test Cases ---

class TestPetAPI:

    # 1. [Positive] 200 OK with a perfect, complete payload.
    def test_add_pet_success(self, api_client, auth_headers):
        payload = create_valid_pet_payload()
        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        response = api_client.post(f"{BASE_URL}/pet", json=payload, headers=headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data == payload
        assert "id" in response_data
        assert response_data["id"] == payload["id"]
        assert "name" in response_data
        assert response_data["name"] == payload["name"]
        assert "status" in response_data
        assert response_data["status"] == payload["status"]

    # 2. [Negative] 400/405 Invalid input (missing required fields).
    @pytest.mark.parametrize(
        "missing_field",
        [
            "name",
            "photoUrls"
        ]
    )
    def test_add_pet_missing_required_field(self, api_client, auth_headers, missing_field):
        payload = create_valid_pet_payload()
        del payload[missing_field]

        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        response = api_client.post(f"{BASE_URL}/pet", json=payload, headers=headers)

        # The API spec indicates 405 for invalid input.
        assert response.status_code == 405
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert missing_field in response_data["message"]

    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    @pytest.mark.parametrize(
        "field, invalid_value",
        [
            ("name", 123),  # Integer instead of string
            ("name", ""),   # Empty string (depending on API implementation, might be valid or invalid)
            ("status", "invalid_status"), # Invalid enum value
            ("id", "abc") # String instead of integer
        ]
    )
    def test_add_pet_invalid_data_type_or_value(self, api_client, auth_headers, field, invalid_value):
        payload = create_valid_pet_payload()
        if field == "photoUrls":
            payload[field] = [123] # Array of integers instead of strings
        elif field == "category":
            payload[field] = "not_an_object"
        elif field == "tags":
            payload[field] = [{"name": "tag1", "extra_field": "value"}]
        else:
            payload[field] = invalid_value

        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        response = api_client.post(f"{BASE_URL}/pet", json=payload, headers=headers)

        # The API spec indicates 405 for validation exceptions.
        assert response.status_code == 405
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert field in response_data["message"]

    # 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    @pytest.mark.parametrize(
        "headers_to_use",
        [
            "invalid_auth_headers",
            "missing_auth_headers"
        ]
    )
    def test_add_pet_unauthorized(self, api_client, request, headers_to_use):
        payload = create_valid_pet_payload()
        auth_headers_fixture = request.getfixturevalue(headers_to_use)
        headers = {
            "Content-Type": "application/json",
            **auth_headers_fixture
        }
        response = api_client.post(f"{BASE_URL}/pet", json=payload, headers=headers)

        # The OpenAPI spec doesn't explicitly define 401/403 for this endpoint,
        # but it shows a security scheme 'petstore_auth'.
        # Typically, missing or invalid auth leads to 401 or 403.
        # We'll assert for a common unauthorized status code.
        assert response.status_code in [401, 403]
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert "authentication" in response_data["message"].lower() or "unauthorized" in response_data["message"].lower()

    # Test for PUT operation - update an existing pet
    def test_update_pet_success(self, api_client, auth_headers):
        # First, add a pet to ensure it exists
        initial_payload = create_valid_pet_payload()
        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        post_response = api_client.post(f"{BASE_URL}/pet", json=initial_payload, headers=headers)
        assert post_response.status_code == 200

        # Now, update the pet
        updated_payload = initial_payload.copy()
        updated_payload["name"] = "BuddyUpdated"
        updated_payload["status"] = "sold"

        put_response = api_client.put(f"{BASE_URL}/pet", json=updated_payload, headers=headers)
        assert put_response.status_code == 200
        response_data = put_response.json()
        assert response_data == updated_payload
        assert "name" in response_data
        assert response_data["name"] == "BuddyUpdated"
        assert "status" in response_data
        assert response_data["status"] == "sold"

    def test_update_pet_not_found(self, api_client, auth_headers):
        payload = create_valid_pet_payload()
        payload["id"] = -1 # Non-existent ID
        payload["name"] = "NonExistentPet"

        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        response = api_client.put(f"{BASE_URL}/pet", json=payload, headers=headers)

        assert response.status_code == 404
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert str(payload["id"]) in response_data["message"] # ID might be in message

    def test_update_pet_invalid_id(self, api_client, auth_headers):
        payload = create_valid_pet_payload()
        payload["id"] = "invalid_id_type" # Invalid type for ID
        payload["name"] = "InvalidIdPet"

        headers = {
            "Content-Type": "application/json",
            **auth_headers
        }
        response = api_client.put(f"{BASE_URL}/pet", json=payload, headers=headers)

        assert response.status_code == 400
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert "Invalid ID supplied" in response_data["message"]

    def test_update_pet_unauthorized(self, api_client, request, headers_to_use):
        payload = create_valid_pet_payload()
        auth_headers_fixture = request.getfixturevalue(headers_to_use)
        headers = {
            "Content-Type": "application/json",
            **auth_headers_fixture
        }
        response = api_client.put(f"{BASE_URL}/pet", json=payload, headers=headers)

        assert response.status_code in [401, 403]
        response_data = response.json()
        assert "code" in response_data
        assert "message" in response_data
        assert "authentication" in response_data["message"].lower() or "unauthorized" in response_data["message"].lower()