import pytest
import requests
import uuid

BASE_URL = "https://petstore.swagger.io/v2"

def generate_unique_pet_data():
    unique_id = uuid.uuid4().int % 1000000000
    return {
        "id": unique_id,
        "category": {"id": 1, "name": "Dogs"},
        "name": f"Buddy_{unique_id}",
        "photoUrls": ["https://example.com/buddy.jpg"],
        "tags": [{"id": 1, "name": "friendly"}],
        "status": "available"
    }

def create_pet(pet_data):
    response = requests.post(f"{BASE_URL}/pet", json=pet_data)
    if response.status_code == 200:
        return response.json()
    return None

def delete_pet(pet_id, api_key=None):
    headers = {}
    if api_key:
        headers['api_key'] = api_key
    response = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers=headers)
    return response.status_code

@pytest.fixture(scope="module")
def setup_pet():
    pet_data = generate_unique_pet_data()
    created_pet = create_pet(pet_data)
    if created_pet:
        yield created_pet
        delete_pet(created_pet['id'])
    else:
        pytest.fail("Failed to create a pet for testing.")

@pytest.fixture
def get_api_key():
    return "special-key" # Replace with a valid API key if needed for actual authorization

class TestPetEndpoint:

    def test_get_pet_by_id_success(self, setup_pet):
        pet_id = setup_pet['id']
        response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert response.status_code == 200
        assert response.json()['id'] == pet_id
        assert response.json()['name'] == setup_pet['name']

    def test_get_pet_by_id_not_found(self):
        non_existent_id = 9999999999999
        response = requests.get(f"{BASE_URL}/pet/{non_existent_id}")
        assert response.status_code == 404

    def test_get_pet_by_id_invalid_id(self):
        invalid_id = "abc"
        response = requests.get(f"{BASE_URL}/pet/{invalid_id}")
        assert response.status_code == 400

    def test_update_pet_with_form_success(self, setup_pet):
        pet_id = setup_pet['id']
        new_name = f"Updated_{setup_pet['name']}"
        new_status = "sold"
        data = {'name': new_name, 'status': new_status}
        response = requests.post(f"{BASE_URL}/pet/{pet_id}", data=data)
        assert response.status_code == 200

        # Verify the update by getting the pet
        get_response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert get_response.status_code == 200
        updated_pet = get_response.json()
        assert updated_pet['name'] == new_name
        assert updated_pet['status'] == new_status

    def test_update_pet_with_form_invalid_id(self):
        invalid_id = "xyz"
        data = {'name': 'TestName', 'status': 'available'}
        response = requests.post(f"{BASE_URL}/pet/{invalid_id}", data=data)
        assert response.status_code == 405 # Swagger spec indicates 405 for invalid input

    def test_update_pet_with_form_pet_not_found(self):
        non_existent_id = 123456789012345
        data = {'name': 'TestName', 'status': 'available'}
        response = requests.post(f"{BASE_URL}/pet/{non_existent_id}", data=data)
        assert response.status_code == 404 # Assuming server returns 404 if pet doesn't exist

    def test_delete_pet_success(self, setup_pet, get_api_key):
        pet_id = setup_pet['id']
        response = delete_pet(pet_id, api_key=get_api_key)
        assert response == 200

        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/pet/{pet_id}")
        assert get_response.status_code == 404

    def test_delete_pet_not_found(self, get_api_key):
        non_existent_id = 111111111111111
        response = delete_pet(non_existent_id, api_key=get_api_key)
        assert response == 404

    def test_delete_pet_invalid_id(self, get_api_key):
        invalid_id = "def"
        response = delete_pet(invalid_id, api_key=get_api_key)
        assert response == 400

    def test_delete_pet_unauthorized(self):
        # Assuming a pet exists, but we don't provide an API key or an invalid one
        # First, create a pet to ensure it exists for this test
        pet_data = generate_unique_pet_data()
        created_pet = create_pet(pet_data)
        if not created_pet:
            pytest.fail("Failed to create a pet for unauthorized delete test.")
        pet_id = created_pet['id']

        try:
            response_no_key = requests.delete(f"{BASE_URL}/pet/{pet_id}")
            # The behavior here might vary depending on the API's strictness for security definitions.
            # If it's optional and defaults to an allowed state, this might not be 401/403.
            # If it requires a key even for testing, it might be 401 or 403.
            # For this example, let's assume a missing key leads to a failure (e.g., 401 or 403)
            # or the delete operation fails in some other way if auth is truly required.
            # If the API allows deletion without a key, this test might need adjustment or removal.
            # We'll assert for a non-200 status code, implying authorization issues or failure.
            assert response_no_key.status_code != 200

            response_invalid_key = requests.delete(f"{BASE_URL}/pet/{pet_id}", headers={'api_key': 'invalid-key'})
            assert response_invalid_key.status_code != 200
        finally:
            # Clean up the created pet, attempting deletion even if the test failed
            delete_pet(pet_id, api_key="special-key") # Use a known good key for cleanup if available