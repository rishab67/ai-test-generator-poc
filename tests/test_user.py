import pytest
import requests
import json
import uuid

BASE_URL = "https://petstore.swagger.io/v2"

def get_base_user_payload():
    """Generates a complete and unique user payload."""
    unique_suffix = uuid.uuid4().hex
    return {
        "id": 0, # Often ignored or assigned by server for creation
        "username": f"testuser_{unique_suffix}",
        "firstName": "Jane",
        "lastName": "Doe",
        "email": f"jane.doe.{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "phone": "987-654-3210",
        "userStatus": 1 # Example: 1 for active
    }

class TestCreateUserEndpoint:

    # 1. [Positive] 200 OK with a perfect, complete payload.
    def test_create_user_positive_complete_payload(self):
        url = f"{BASE_URL}/user"
        payload = get_base_user_payload()
        
        response = requests.post(url, json=payload)
        
        assert response.status_code == 200, \
            f"Positive test failed: Expected status code 200, but got {response.status_code}. Response: {response.text}"
        
        # Petstore's create user typically returns a generic ApiResponse for success.
        # Example: {"code": 200, "type": "unknown", "message": "123"} where "123" is an ID.
        try:
            response_json = response.json()
            assert "code" in response_json, "Response JSON missing 'code' field."
            assert response_json["code"] == 200, \
                f"Expected response code 200 in JSON, but got {response_json['code']}."
            assert "type" in response_json, "Response JSON missing 'type' field."
            # Petstore often returns 'unknown' for type on successful user creation.
            assert response_json["type"] == "unknown", \
                f"Expected response type 'unknown', but got {response_json['type']}."
            assert "message" in response_json, "Response JSON missing 'message' field."
            assert response_json["message"].isdigit(), \
                f"Expected 'message' to be a numeric user ID, but got {response_json['message']}."
        except json.JSONDecodeError:
            pytest.fail(f"Response is not valid JSON: {response.text}")


    # 2. [Negative] 400/405 Invalid input (missing required fields).
    # Note: Petstore's /user endpoint is often lenient and might return 200 even for
    # logically required fields (e.g., username, email, password) if not explicitly
    # enforced on the server-side. As an SDET/Security Tester, we expect 400/405
    # for missing critical data to ensure robust validation. This test will
    # intentionally fail if the API returns 200, highlighting a potential API design flaw.
    @pytest.mark.parametrize("missing_field", ["username", "email", "password"])
    def test_create_user_negative_missing_required_fields(self, missing_field):
        url = f"{BASE_URL}/user"
        payload = get_base_user_payload()
        
        # Remove the specified field
        payload.pop(missing_field, None)
        
        response = requests.post(url, json=payload)
        
        assert response.status_code in [400, 405], \
            f"Negative test failed: Expected status code 400 or 405 for missing '{missing_field}', " \
            f"but got {response.status_code}. This indicates the API might not enforce " \
            f"'{missing_field}' as required, a potential validation gap. Response: {response.text}"
        
        if response.status_code in [400, 405]:
            try:
                response_json = response.json()
                assert "code" in response_json
                assert "type" in response_json
                assert "message" in response_json
                assert "error" in response_json["type"].lower() or "bad request" in response_json["message"].lower()
            except json.JSONDecodeError:
                assert "Error" in response.text or "Bad Request" in response.text or "invalid" in response.text


    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    # Similar to missing fields, Petstore's /user endpoint can be lenient, potentially coercing types
    # or returning 200 for invalid data. This test asserts for 400/405 to highlight
    # a lack of strict input validation, which is a common security/robustness concern.
    @pytest.mark.parametrize("field, invalid_value", [
        ("username", 12345),  # int where string expected
        ("email", ""),        # empty string, often invalid for email format
        ("password", 11111),  # int where string expected
        ("firstName", ""),    # empty string for non-required string
        ("lastName", 98765),  # int where string expected
        ("userStatus", "invalid_status"), # string where int expected
        ("id", "not_an_int")  # string where int expected
    ])
    def test_create_user_negative_boundary_invalid_data_types_and_empty_strings(self, field, invalid_value):
        url = f"{BASE_URL}/user"
        payload = get_base_user_payload()
        
        payload[field] = invalid_value
        
        response = requests.post(url, json=payload)
        
        assert response.status_code in [400, 405], \
            f"Negative test failed: Expected status code 400 or 405 for invalid input for '{field}' (value: '{invalid_value}'), " \
            f"but got {response.status_code}. This indicates the API might not strictly validate " \
            f"data types/formats. Response: {response.text}"
        
        if response.status_code in [400, 405]:
            try:
                response_json = response.json()
                assert "code" in response_json
                assert "type" in response_json
                assert "message" in response_json
            except json.JSONDecodeError:
                assert "Error" in response.text or "Bad Request" in response.text or "invalid" in response.text


    # 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    # The OpenAPI description states: "This can only be done by the logged in user."
    # This test simulates an unauthenticated request. If the API returns 200, it's a security finding,
    # as user creation would be possible without meeting the documented security requirement.
    def test_create_user_security_unauthorized(self):
        url = f"{BASE_URL}/user"
        payload = get_base_user_payload()
        
        # No authentication headers are sent, simulating an unauthenticated request.
        response = requests.post(url, json=payload)
        
        assert response.status_code in [401, 403], \
            f"Security test failed: Expected status code 401 or 403 for an unauthenticated request, " \
            f"but got {response.status_code}. This potentially indicates a security bypass, " \
            f"allowing user creation without a 'logged in user' as specified. Response: {response.text}"

        if response.status_code in [401, 403]:
            try:
                response_json = response.json()
                assert "code" in response_json
                assert "type" in response_json
                assert "message" in response_json
                assert "unauthorized" in response_json["message"].lower() or "forbidden" in response_json["message"].lower()
            except json.JSONDecodeError:
                assert "Unauthorized" in response.text or "Forbidden" in response.text