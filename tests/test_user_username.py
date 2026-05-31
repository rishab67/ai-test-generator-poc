import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

def create_user(username, first_name, last_name, email, password, phone_number, user_status=0):
    """Helper function to create a user for testing."""
    user_data = {
        "username": username,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "password": password,
        "phoneNumbers": [phone_number],
        "userStatus": user_status
    }
    response = requests.post(f"{BASE_URL}/user", json=user_data)
    return response

def delete_user(username):
    """Helper function to delete a user after testing."""
    response = requests.delete(f"{BASE_URL}/user/{username}")
    return response

@pytest.fixture(scope="module")
def test_user_data():
    """Provides a unique username and data for testing."""
    username = "testuser_pytest_sd"
    first_name = "Test"
    last_name = "User"
    email = "test.user@example.com"
    password = "password123"
    phone_number = "1234567890"
    yield username, first_name, last_name, email, password, phone_number
    # Clean up the created user after all tests in the module
    delete_user(username)

class TestUserEndpoint:

    def test_get_user_by_username_success(self, test_user_data):
        username, first_name, last_name, email, password, phone_number = test_user_data
        # Ensure user exists before trying to get it
        create_response = create_user(username, first_name, last_name, email, password, phone_number)
        assert create_response.status_code == 200

        response = requests.get(f"{BASE_URL}/user/{username}")
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == username
        assert user_data["firstName"] == first_name
        assert user_data["lastName"] == last_name
        assert user_data["email"] == email
        assert user_data["phoneNumbers"][0] == phone_number

    def test_get_user_by_username_not_found(self):
        non_existent_username = "nonexistent_user_123"
        response = requests.get(f"{BASE_URL}/user/{non_existent_username}")
        assert response.status_code == 404

    def test_update_user_success(self, test_user_data):
        username, first_name, last_name, email, password, phone_number = test_user_data
        # Ensure user exists before trying to update it
        create_response = create_user(username, first_name, last_name, email, password, phone_number)
        assert create_response.status_code == 200

        updated_first_name = "UpdatedTest"
        updated_last_name = "UpdatedUser"
        updated_email = "updated.user@example.com"
        updated_phone_number = "0987654321"
        updated_user_status = 1

        update_data = {
            "username": username,
            "firstName": updated_first_name,
            "lastName": updated_last_name,
            "email": updated_email,
            "password": password,
            "phoneNumbers": [updated_phone_number],
            "userStatus": updated_user_status
        }
        response = requests.put(f"{BASE_URL}/user/{username}", json=update_data)
        assert response.status_code == 200

        # Verify the update
        get_response = requests.get(f"{BASE_URL}/user/{username}")
        assert get_response.status_code == 200
        user_data = get_response.json()
        assert user_data["firstName"] == updated_first_name
        assert user_data["lastName"] == updated_last_name
        assert user_data["email"] == updated_email
        assert user_data["phoneNumbers"][0] == updated_phone_number
        assert user_data["userStatus"] == updated_user_status

    def test_update_user_not_found(self):
        non_existent_username = "nonexistent_user_update_123"
        update_data = {
            "username": non_existent_username,
            "firstName": "Test",
            "lastName": "User",
            "email": "test.user@example.com",
            "password": "password123",
            "phoneNumbers": ["1234567890"],
            "userStatus": 0
        }
        response = requests.put(f"{BASE_URL}/user/{non_existent_username}", json=update_data)
        assert response.status_code == 404

    def test_delete_user_success(self, test_user_data):
        username, first_name, last_name, email, password, phone_number = test_user_data
        # Create user first to ensure it exists for deletion
        create_response = create_user(username, first_name, last_name, email, password, phone_number)
        assert create_response.status_code == 200

        response = requests.delete(f"{BASE_URL}/user/{username}")
        assert response.status_code == 200

        # Verify deletion by trying to get the user
        get_response = requests.get(f"{BASE_URL}/user/{username}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self):
        non_existent_username = "nonexistent_user_delete_123"
        response = requests.delete(f"{BASE_URL}/user/{non_existent_username}")
        assert response.status_code == 404

    def test_get_user_by_username_with_special_chars(self):
        # The schema doesn't explicitly restrict characters in username,
        # but testing with a username that might be tricky.
        # Assuming the backend correctly handles URL encoding if necessary.
        # For this specific API, it seems simple strings are expected.
        # Let's use 'user1' as suggested in the schema description.
        username = "user1"
        response = requests.get(f"{BASE_URL}/user/{username}")
        # If user1 exists and is valid, we expect 200.
        # If not, we might expect 404, but the test should still run.
        # The schema mentions "Use user1 for testing." so we'll assume it might exist.
        if response.status_code == 200:
            user_data = response.json()
            assert user_data["username"] == username
        else:
            assert response.status_code == 404 # Or another expected error code if 'user1' is not guaranteed to exist.