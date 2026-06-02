import requests
import pytest
import uuid

BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = "/user/createWithArray"
URL = f"{BASE_URL}{ENDPOINT}"

def create_valid_user_payload(index=1):
    unique_suffix = uuid.uuid4().hex[:8]
    return {
        "id": index,
        "username": f"testuser_{unique_suffix}_{index}",
        "firstName": f"FirstName_{index}",
        "lastName": f"LastName_{index}",
        "email": f"user{index}@{unique_suffix}.com",
        "password": f"password{index}",
        "phone": f"123-456-789{index}",
        "userStatus": 1
    }

class TestCreateUsersWithArray:

    def test_create_users_200_ok_complete_payload(self):
        """
        [Positive] Tests creating a list of users with a complete and valid payload,
        expecting a 200 OK status code.
        """
        users_payload = [
            create_valid_user_payload(1),
            create_valid_user_payload(2)
        ]
        headers = {"Content-Type": "application/json"}
        response = requests.post(URL, json=users_payload, headers=headers)

        assert response.status_code == 200, f"Expected Status Code 200, got {response.status_code}. Response: {response.text}"
        assert "successful operation" in response.text or response.text == "", \
            f"Expected 'successful operation' or empty response, got: {response.text}"

    @pytest.mark.parametrize("missing_field_user_payload", [
        # Missing 'username'
        ([{
            "id": 101,
            "firstName": "MissingUser",
            "lastName": "Field",
            "email": "missing@example.com",
            "password": "password123",
            "phone": "111-222-3333",
            "userStatus": 1
        }]),
        # Missing 'id'
        ([{
            "username": "no_id_user",
            "firstName": "NoId",
            "lastName": "User",
            "email": "noid@example.com",
            "password": "password123",
            "phone": "111-222-3333",
            "userStatus": 1
        }]),
        # Sending an empty user object
        ([{}]),
        # Sending a list with one valid and one invalid user
        ([create_valid_user_payload(3), {}]),
    ])
    def test_create_users_400_missing_required_fields(self, missing_field_user_payload):
        """
        [Negative] Tests creating users with payloads missing assumed 'required' fields,
        expecting a 400 Bad Request status.
        """
        headers = {"Content-Type": "application/json"}
        response = requests.post(URL, json=missing_field_user_payload, headers=headers)

        assert response.status_code == 400, \
            f"Expected Status Code 400, got {response.status_code}. Response: {response.text}"
        assert "bad input" in response.text.lower() or "error" in response.text.lower() or "invalid" in response.text.lower(), \
            f"Expected error message for 400, got: {response.text}"

    @pytest.mark.parametrize("invalid_payload", [
        # Sending an integer instead of a string for username
        ([{
            "id": 1,
            "username": 12345,
            "firstName": "Boundary", "lastName": "Test", "email": "bt@example.com",
            "password": "pass", "phone": "123", "userStatus": 1
        }]),
        # Sending an empty string for username
        ([{
            "id": 2,
            "username": "",
            "firstName": "Boundary", "lastName": "Test", "email": "bt2@example.com",
            "password": "pass", "phone": "123", "userStatus": 1
        }]),
        # Sending a non-array payload (e.g., a single user object directly)
        (create_valid_user_payload(4)),
        # Sending an empty list (functionally invalid for "create" operation)
        ([]),
        # Sending a list with a non-object element
        ([create_valid_user_payload(5), "not_an_object"]),
    ])
    def test_create_users_400_boundary_invalid_data_types_and_formats(self, invalid_payload):
        """
        [Negative] Tests boundary conditions and invalid data types/formats,
        expecting a 400 Bad Request.
        """
        headers = {"Content-Type": "application/json"}
        response = requests.post(URL, json=invalid_payload, headers=headers)

        assert response.status_code == 400, \
            f"Expected Status Code 400, got {response.status_code}. Response: {response.text}"
        assert "bad input" in response.text.lower() or "error" in response.text.lower() or "invalid" in response.text.lower() or "syntax" in response.text.lower(), \
            f"Expected error message for 400, got: {response.text}"

    def test_create_users_400_non_json_payload(self):
        """
        [Negative] Tests sending a non-JSON payload, expecting a 400 Bad Request.
        """
        headers = {"Content-Type": "text/plain"}
        response = requests.post(URL, data="this is not json", headers=headers)

        assert response.status_code == 400, \
            f"Expected Status Code 400, got {response.status_code}. Response: {response.text}"
        assert "bad input" in response.text.lower() or "error" in response.text.lower() or "invalid" in response.text.lower() or "syntax" in response.text.lower(), \
            f"Expected error message for 400, got: {response.text}"


    @pytest.mark.parametrize("auth_headers", [
        # No authentication headers
        ({}),
        # Invalid Bearer Token
        ({"Authorization": "Bearer invalid_token_123"}),
        # Invalid Basic Auth
        ({"Authorization": "Basic YWRtaW46aW52YWxpZFBhc3N3b3Jk"}),
    ])
    def test_create_users_security_unauthorized_access_simulation(self, auth_headers):
        """
        [Security] Simulates unauthorized access attempts with missing or invalid authentication headers.
        As a security best practice, protected endpoints should return 401 Unauthorized or 403 Forbidden.
        This test asserts for that expected security behavior.
        """
        users_payload = [create_valid_user_payload(10)]
        headers = {"Content-Type": "application/json"}
        headers.update(auth_headers)

        response = requests.post(URL, json=users_payload, headers=headers)

        assert response.status_code in [401, 403], \
            f"Expected Status Code 401 or 403 for unauthorized access simulation, " \
            f"but got {response.status_code}. If the API returned 200, this indicates " \
            f"a potential security flaw where an endpoint that should be protected is not. " \
            f"Response: {response.text}"