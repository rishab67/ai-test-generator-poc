import requests
import pytest
import datetime
import uuid
import random

BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = "/store/order"
URL = f"{BASE_URL}{ENDPOINT}"

@pytest.fixture(scope="module")
def api_client():
    """Fixture for the API client (requests session)."""
    return requests.Session()

def generate_valid_order_payload(order_id=None, pet_id=None, quantity=None, status=None):
    """Generates a valid order payload."""
    return {
        "id": order_id if order_id is not None else random.randint(1, 100000),
        "petId": pet_id if pet_id is not None else random.randint(1, 100000),
        "quantity": quantity if quantity is not None else random.randint(1, 10),
        "shipDate": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        "status": status if status is not None else random.choice(["placed", "approved", "delivered"]),
        "complete": random.choice([True, False])
    }

class TestStoreOrderEndpoint:

    def test_1_positive_200_complete_payload(self, api_client):
        """
        [Positive] 200 OK with a perfect, complete payload.
        """
        payload = generate_valid_order_payload()
        headers = {"Content-Type": "application/json"}
        response = api_client.post(URL, json=payload, headers=headers)

        assert response.status_code == 200, f"Expected Status Code 200, got {response.status_code}"
        response_body = response.json()

        assert isinstance(response_body, dict), "Response body is not a dictionary."
        assert "id" in response_body, "Response missing 'id' field."
        assert "petId" in response_body, "Response missing 'petId' field."
        assert "quantity" in response_body, "Response missing 'quantity' field."
        assert "shipDate" in response_body, "Response missing 'shipDate' field."
        assert "status" in response_body, "Response missing 'status' field."
        assert "complete" in response_body, "Response missing 'complete' field."

        assert isinstance(response_body["id"], int), "id is not an integer."
        assert isinstance(response_body["petId"], int), "petId is not an integer."
        assert isinstance(response_body["quantity"], int), "quantity is not an integer."
        assert isinstance(response_body["shipDate"], str), "shipDate is not a string."
        assert isinstance(response_body["status"], str), "status is not a string."
        assert isinstance(response_body["complete"], bool), "complete is not a boolean."

        # Verify that some submitted data is reflected in the response (common behavior)
        assert response_body["id"] == payload["id"]
        assert response_body["petId"] == payload["petId"]
        assert response_body["quantity"] == payload["quantity"]
        assert response_body["status"] == payload["status"]

    @pytest.mark.parametrize("missing_field", ["petId", "quantity", "shipDate", "status"])
    def test_2_negative_400_missing_required_fields(self, api_client, missing_field):
        """
        [Negative] 400 Invalid input (missing required fields).
        """
        payload = generate_valid_order_payload()
        del payload[missing_field]
        headers = {"Content-Type": "application/json"}
        response = api_client.post(URL, json=payload, headers=headers)

        assert response.status_code == 400, f"Expected Status Code 400 for missing '{missing_field}', got {response.status_code}"
        response_body = response.json()
        assert isinstance(response_body, dict), "Response body is not a dictionary."
        assert "message" in response_body or "type" in response_body, "Error response missing expected fields."

    @pytest.mark.parametrize(
        "field, invalid_value, expected_type",
        [
            ("petId", "not_an_int", "string"),
            ("petId", None, "null"),
            ("quantity", "not_an_int", "string"),
            ("quantity", -5, "negative_int"),
            ("shipDate", "invalid-date-format", "string"),
            ("shipDate", 12345, "integer"),
            ("status", 123, "integer"),
            ("status", "", "empty_string"),
            ("complete", "not_a_bool", "string"),
            ("id", "not_an_int", "string"),
        ]
    )
    def test_3_negative_400_boundary_invalid_types_and_values(self, api_client, field, invalid_value, expected_type):
        """
        [Negative] 400 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
        """
        payload = generate_valid_order_payload()
        
        if expected_type == "negative_int":
            payload[field] = invalid_value # For quantity specifically
        elif expected_type == "null":
            payload[field] = None
        else:
            payload[field] = invalid_value

        headers = {"Content-Type": "application/json"}
        response = api_client.post(URL, json=payload, headers=headers)
        
        # Petstore API often returns 500 for schema validation failures with incorrect types.
        # As an SDET, we test for both 400 (client error) and 500 (server processing error due to bad input).
        assert response.status_code in [400, 500], \
            f"Expected Status Code 400 or 500 for '{field}' with '{expected_type}' '{invalid_value}', got {response.status_code}"
        
        response_body = response.json()
        assert isinstance(response_body, dict), "Response body is not a dictionary."
        assert "message" in response_body or "type" in response_body, "Error response missing expected fields."

    def test_4_security_401_missing_authentication(self, api_client):
        """
        [Security] 401/403 Unauthorized (simulate missing authentication headers).
        """
        payload = generate_valid_order_payload()
        # Simulate missing Authorization header
        headers = {"Content-Type": "application/json"} # No auth header
        response = api_client.post(URL, json=payload, headers=headers)

        # The Swagger Petstore public API might return 200 even without auth,
        # but as a security test, we assert for 401/403 as per requirement for secured APIs.
        assert response.status_code in [401, 403], \
            f"Expected Status Code 401 or 403 for missing authentication, got {response.status_code}"

    def test_4_security_403_invalid_authentication(self, api_client):
        """
        [Security] 401/403 Unauthorized (simulate invalid authentication headers).
        """
        payload = generate_valid_order_payload()
        # Simulate invalid Authorization header
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_12345"
        }
        response = api_client.post(URL, json=payload, headers=headers)

        # The Swagger Petstore public API might return 200 even with invalid auth,
        # but as a security test, we assert for 401/403 as per requirement for secured APIs.
        assert response.status_code in [401, 403], \
            f"Expected Status Code 401 or 403 for invalid authentication, got {response.status_code}"