import pytest
import requests
import json
import time

BASE_URL = "https://petstore.swagger.io/v2"
API_KEY_HEADER = {"api_key": "special-key"} # Known key for write/delete access

# --- Helper function for pet creation (used by fixture and some tests) ---
def create_test_pet():
    pet_data = {
        "id": int(time.time()), # Unique ID based on timestamp
        "category": {"id": 1, "name": "Dogs"},
        "name": "doggie_test_temp",
        "photoUrls": ["string"],
        "tags": [{"id": 0, "name": "tag1"}],
        "status": "available"
    }
    response = requests.post(f"{BASE_URL}/pet", json=pet_data, headers=API_KEY_HEADER)
    response.raise_for_status() # Ensure pet creation is successful
    return response.json()

# --- Fixture to create and cleanup a pet for tests that need an existing pet ---
@pytest.fixture(scope="module")
def pet_id_fixture():
    print("\nSetting up: Creating a test pet...")
    pet = create_test_pet()
    pet_id = pet["id"]
    yield pet_id
    print(f"\nTeardown: Deleting test pet with ID {pet_id}...")
    # Attempt to delete the pet if it still exists
    requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=API_KEY_HEADER)

# --- Test class for /pet/{petId} ---
class TestPetByIdEndpoint:

    # ----------------------------------------------------------------------
    # GET /pet/{petId} - Find pet by ID
    # ----------------------------------------------------------------------

    def test_get_pet_by_id_positive_200_ok(self, pet_id_fixture):
        """
        [Positive] 200 OK with a perfect, complete payload for GET /pet/{petId}.
        """
        pet_id = pet_id_fixture
        response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert response.status_code == 200, \
            f"Expected status 200, but got {response.status_code}. Response: {response.text}"
        
        pet_data = response.json()
        assert isinstance(pet_data, dict)
        assert pet_data["id"] == pet_id
        assert "name" in pet_data
        assert "status" in pet_data
        assert "category" in pet_data
        assert "photoUrls" in pet_data
        assert "tags" in pet_data
        assert isinstance(pet_data["photoUrls"], list)
        assert isinstance(pet_data["tags"], list)
        assert pet_data["status"] == "available" # Default status from creation


    @pytest.mark.parametrize("invalid_id, expected_status, expected_error_msg", [
        ("invalidID", 400, "Invalid ID supplied"), # String ID
        ("123.45", 400, "Invalid ID supplied"),    # Float as string
        ("0", 400, "Invalid ID supplied"),          # Zero as string
        ("-1", 400, "Invalid ID supplied"),         # Negative as string
        (str(9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999), 400, "Invalid ID supplied"), # Very large number as string, might overflow or be treated as invalid
        (9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999, 404, "Pet not found"), # Very large int, likely non-existent
    ])
    def test_get_pet_by_id_negative_boundary_invalid_id_format(self, invalid_id, expected_status, expected_error_msg):
        """
        [Negative] 400/404 Boundary testing for petId (e.g., non-integer, zero, negative, very large) for GET.
        """
        response = requests.get(f"{BASE_URL}/pet/{invalid_id}")
        assert response.status_code == expected_status, \
            f"Expected status {expected_status} for ID '{invalid_id}', but got {response.status_code}. Response: {response.text}"
        assert expected_error_msg in response.text


    def test_get_pet_by_id_negative_404_pet_not_found(self):
        """
        [Negative] 404 Pet not found for a non-existent but valid ID (GET).
        """
        non_existent_id = 123456789012345 # A large, likely non-existent valid integer ID
        response = requests.get(f"{BASE_URL}/pet/{non_existent_id}")
        assert response.status_code == 404
        assert "Pet not found" in response.text


    def test_get_pet_by_id_security_no_auth_expected_200(self, pet_id_fixture):
        """
        [Security] Test GET /pet/{petId} without API key.
        Schema indicates api_key is optional for GET, so 200 is expected.
        """
        pet_id = pet_id_fixture
        response = requests.get(f"{BASE_URL}/pet/{pet_id}") # No API key header
        assert response.status_code == 200, \
            f"Expected status 200 (api_key optional for GET), but got {response.status_code}. Response: {response.text}"
        assert response.json()["id"] == pet_id # Ensure pet data is returned

    # ----------------------------------------------------------------------
    # POST /pet/{petId} - Updates a pet in the store with form data
    # ----------------------------------------------------------------------

    def test_post_pet_by_id_positive_200_ok(self, pet_id_fixture):
        """
        [Positive] 200 OK with complete form data for POST /pet/{petId}.
        Updates pet's name and status.
        """
        pet_id = pet_id_fixture
        updated_name = "UpdatedDogName"
        updated_status = "sold"
        form_data = {
            "name": updated_name,
            "status": updated_status
        }
        
        response = requests.post(
            f"{BASE_URL}/pet/{pet_id}", 
            data=form_data, 
            headers={"Content-Type": "application/x-www-form-urlencoded", **API_KEY_HEADER}
        )
        # Petstore API actually returns 200 for successful updates via POST form data
        assert response.status_code == 200, \
            f"Expected status 200 for successful update, but got {response.status_code}. Response: {response.text}"
        
        # Verify the update via GET
        time.sleep(1) # Give API a moment to propagate, if needed
        get_response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert get_response.status_code == 200
        updated_pet = get_response.json()
        assert updated_pet["name"] == updated_name
        assert updated_pet["status"] == updated_status


    @pytest.mark.parametrize("invalid_id, expected_status, expected_error_msg", [
        ("abc", 400, "Invalid ID supplied"), # String ID
        ("0", 400, "Invalid ID supplied"),   # Zero as string
        ("-1", 400, "Invalid ID supplied"),  # Negative as string
        (123456789012345, 404, "Pet not found"), # Non-existent ID
    ])
    def test_post_pet_by_id_negative_invalid_pet_id_in_path(self, invalid_id, expected_status, expected_error_msg):
        """
        [Negative] 400/404 for POST /pet/{petId} with invalid petId in path.
        """
        form_data = {"name": "test", "status": "available"}
        response = requests.post(
            f"{BASE_URL}/pet/{invalid_id}",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded", **API_KEY_HEADER}
        )
        assert response.status_code == expected_status
        assert expected_error_msg in response.text

    @pytest.mark.parametrize("form_data_input, expected_name, expected_status", [
        ({"name": "", "status": "available"}, "", "available"), # Empty string for name
        ({"name": "NewName", "status": ""}, "NewName", ""),     # Empty string for status
        ({"name": "123", "status": "pending"}, "123", "pending"), # Number as string for name
        ({"name": "A very very very long name for a pet that should be handled correctly by the system, hopefully it doesn't break anything critical in the database.", "status": "very_long_status_description"},
         "A very very very long name for a pet that should be handled correctly by the system, hopefully it doesn't break anything critical in the database.", "very_long_status_description"), # Long strings
        ({"name": "!@#$%^&*()_+", "status": "`~[]{}|"}, "!@#$%^&*()_+", "`~[]{}|"), # Special characters
    ])
    def test_post_pet_by_id_boundary_form_data_values(self, pet_id_fixture, form_data_input, expected_name, expected_status):
        """
        [Negative]/[Boundary] Boundary testing for formData (name, status) in POST /pet/{petId}.
        Petstore API often accepts empty strings or numbers as strings, and long/special characters.
        """
        pet_id = pet_id_fixture
        response = requests.post(
            f"{BASE_URL}/pet/{pet_id}",
            data=form_data_input,
            headers={"Content-Type": "application/x-www-form-urlencoded", **API_KEY_HEADER}
        )
        assert response.status_code == 200, \
            f"Expected 200 for valid form data, got {response.status_code}. Response: {response.text}"
        
        # Verify the update via GET
        time.sleep(1)
        get_response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert get_response.status_code == 200
        updated_pet = get_response.json()
        assert updated_pet["name"] == expected_name
        assert updated_pet["status"] == expected_status


    def test_post_pet_by_id_security_403_missing_api_key(self, pet_id_fixture):
        """
        [Security] 403 Forbidden for POST /pet/{petId} with missing API key.
        """
        pet_id = pet_id_fixture
        form_data = {"name": "UnauthorizedName", "status": "sold"}
        
        response = requests.post(
            f"{BASE_URL}/pet/{pet_id}", 
            data=form_data, 
            headers={"Content-Type": "application/x-www-form-urlencoded"} # Missing API key
        )
        # Petstore V2 returns 403 Forbidden for missing API key on write operations
        assert response.status_code == 403, \
            f"Expected status 403 for missing API key, but got {response.status_code}. Response: {response.text}"
        assert "access denied" in response.text.lower()


    def test_post_pet_by_id_security_403_invalid_api_key(self, pet_id_fixture):
        """
        [Security] 403 Forbidden for POST /pet/{petId} with invalid API key.
        """
        pet_id = pet_id_fixture
        form_data = {"name": "InvalidKeyName", "status": "pending"}
        invalid_api_key_header = {"api_key": "invalid-key"}
        
        response = requests.post(
            f"{BASE_URL}/pet/{pet_id}", 
            data=form_data, 
            headers={"Content-Type": "application/x-www-form-urlencoded", **invalid_api_key_header}
        )
        assert response.status_code == 403, \
            f"Expected status 403 for invalid API key, but got {response.status_code}. Response: {response.text}"
        assert "access denied" in response.text.lower()

    # ----------------------------------------------------------------------
    # DELETE /pet/{petId} - Deletes a pet
    # ----------------------------------------------------------------------

    def test_delete_pet_positive_200_ok(self):
        """
        [Positive] 200 OK for DELETE /pet/{petId} with a valid pet ID and API key.
        Creates a pet and then deletes it.
        """
        # Create a pet specifically for this delete test
        pet_to_delete = create_test_pet()
        pet_id = pet_to_delete["id"]
        
        response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=API_KEY_HEADER)
        # Petstore API returns 200 OK for successful delete
        assert response.status_code == 200, \
            f"Expected status 200 for successful delete, but got {response.status_code}. Response: {response.text}"
        
        # Verify deletion by trying to GET the pet
        time.sleep(1) # Give API a moment to propagate
        get_response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert get_response.status_code == 404, \
            f"Expected 404 after deletion, but got {get_response.status_code}. Response: {get_response.text}"
        assert "Pet not found" in get_response.text


    @pytest.mark.parametrize("invalid_id, expected_status, expected_error_msg", [
        ("abc", 400, "Invalid ID supplied"), # String ID
        ("0", 400, "Invalid ID supplied"),   # Zero as string
        ("-1", 400, "Invalid ID supplied"),  # Negative as string
        (123456789012345, 404, "Pet not found"), # Non-existent ID
    ])
    def test_delete_pet_negative_boundary_invalid_id_format(self, invalid_id, expected_status, expected_error_msg):
        """
        [Negative] 400/404 Boundary testing for petId (e.g., non-integer, zero, negative, non-existent) for DELETE.
        """
        response = requests.delete(f"{BASE_URL}/pet/{invalid_id}", headers=API_KEY_HEADER)
        assert response.status_code == expected_status, \
            f"Expected status {expected_status} for ID '{invalid_id}', but got {response.status_code}. Response: {response.text}"
        assert expected_error_msg in response.text


    def test_delete_pet_security_403_missing_api_key(self):
        """
        [Security] 403 Forbidden for DELETE /pet/{petId} with missing API key.
        """
        # Create a pet specifically for this security test
        pet_to_delete = create_test_pet()
        pet_id = pet_to_delete["id"]
        
        response = requests.delete(f"{BASE_URL}/pet/{pet_id}") # Missing API key
        assert response.status_code == 403, \
            f"Expected status 403 for missing API key, but got {response.status_code}. Response: {response.text}"
        assert "access denied" in response.text.lower()
        
        # Cleanup: Re-delete with API key to ensure test data is cleaned up
        requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=API_KEY_HEADER)


    def test_delete_pet_security_403_invalid_api_key(self):
        """
        [Security] 403 Forbidden for DELETE /pet/{petId} with invalid API key.
        """
        # Create a pet specifically for this security test
        pet_to_delete = create_test_pet()
        pet_id = pet_to_delete["id"]
        invalid_api_key_header = {"api_key": "definitely-not-special"}
        
        response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=invalid_api_key_header)
        assert response.status_code == 403, \
            f"Expected status 403 for invalid API key, but got {response.status_code}. Response: {response.text}"
        assert "access denied" in response.text.lower()

        # Cleanup: Re-delete with valid API key to ensure test data is cleaned up
        requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=API_KEY_HEADER)