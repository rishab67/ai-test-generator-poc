import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

class TestUserLogin:

    def test_successful_login(self):
        username = "testuser"
        password = "testpassword"
        response = requests.get(f"{BASE_URL}/user/login", params={"username": username, "password": password})
        assert response.status_code == 200
        assert "X-Expires-After" in response.headers
        assert "X-Rate-Limit" in response.headers
        assert isinstance(response.headers["X-Rate-Limit"], str) # Schema says int32, but API often returns string
        assert response.text is not None # Schema says string

    def test_invalid_credentials(self):
        username = "invaliduser"
        password = "wrongpassword"
        response = requests.get(f"{BASE_URL}/user/login", params={"username": username, "password": password})
        assert response.status_code == 400

    def test_missing_username(self):
        password = "testpassword"
        response = requests.get(f"{BASE_URL}/user/login", params={"password": password})
        assert response.status_code == 404 # Or other error code indicating missing parameter, depending on API implementation

    def test_missing_password(self):
        username = "testuser"
        response = requests.get(f"{BASE_URL}/user/login", params={"username": username})
        assert response.status_code == 404 # Or other error code indicating missing parameter, depending on API implementation

    def test_empty_username(self):
        username = ""
        password = "testpassword"
        response = requests.get(f"{BASE_URL}/user/login", params={"username": username, "password": password})
        assert response.status_code == 400 # Assuming empty credentials are invalid

    def test_empty_password(self):
        username = "testuser"
        password = ""
        response = requests.get(f"{BASE_URL}/user/login", params={"username": username, "password": password})
        assert response.status_code == 400 # Assuming empty credentials are invalid