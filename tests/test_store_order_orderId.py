import pytest
import requests
import json
from datetime import datetime

# BASE_URL must be hardcoded as specified
BASE_URL = "https://petstore.swagger.io/v2"

@pytest.fixture(scope="module")
def api_base_url():
    return BASE_URL

@pytest.fixture(scope="module")
def headers():
    return {"Content-Type": "application/json", "Accept": "application/json"}

# --- GET /store/order/{orderId} Tests ---

def test_get_order_by_id_200_positive(api_base_url, headers):
    """
    [Positive] 200 OK with a perfect, complete payload for GET /store/order/{orderId}.
    Tests retrieval of an existing order within the valid ID range (1-10).
    Note: For public APIs, order existence can vary. Using orderId=7 as a common example.
    If orderId=7 doesn't exist, this test will fail expecting 200 but receiving 404.
    """
    order_id = 7  # A valid ID likely to exist for positive test
    url = f"{api_base_url}/store/order/{order_id}"
    response = requests.get(url, headers=headers)

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    order = response.json()

    assert isinstance(order, dict), "Response payload is not a dictionary"
    assert "id" in order, "Order ID missing in response"
    assert isinstance(order["id"], int), "Order ID is not an integer"
    assert order["id"] == order_id, "Returned order ID does not match requested ID"

    # Schema validation for other fields (assuming a typical Order structure)
    assert "petId" in order and isinstance(order["petId"], int)
    assert "quantity" in order and isinstance(order["quantity"], int)
    assert "shipDate" in order and isinstance(order["shipDate"], str)
    assert "status" in order and isinstance(order["status"], str)
    assert order["status"] in ["placed", "approved", "delivered"]
    assert "complete" in order and isinstance(order["complete"], bool)

    # Validate shipDate format (ISO 8601 / RFC 3339)
    try:
        datetime.fromisoformat(order["shipDate"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"shipDate '{order['shipDate']}' is not in a valid ISO 8601 format.")

@pytest.mark.parametrize("order_id, expected_status, description", [
    (0, 400, "Order ID below minimum (0) for GET"),
    (11, 400, "Order ID above maximum (11) for GET"),
    ("invalid", 400, "Non-integer Order ID (string) for GET"),
    ("!@#", 400, "Special characters as Order ID for GET"),
    ("", 404, "Empty string as Order ID for GET (malformed URL)"), # Server might respond with 404 for malformed path
    ("10000000000000000000", 400, "Very large integer (out of range/overflow) for GET") # Int64 but still large
])
def test_get_order_by_id_negative_invalid_input_boundary(api_base_url, headers, order_id, expected_status, description):
    """
    [Negative] 400/404 Invalid input/Boundary testing for GET /store/order/{orderId}.
    Covers out-of-range IDs, wrong data types, and malformed inputs.
    """
    url = f"{api_base_url}/store/order/{order_id}" if order_id != "" else f"{api_base_url}/store/order/"
    response = requests.get(url, headers=headers)

    assert response.status_code == expected_status, \
        f"{description}: Expected status code {expected_status}, got {response.status_code} for orderId='{order_id}'"

    # Basic check for error message if 400
    if response.status_code == 400:
        assert isinstance(response.json(), dict), "Error response is not a dictionary"
        assert "message" in response.json() or "type" in response.json(), "Error message or type missing"

def test_get_order_by_id_security_unauthorized(api_base_url, headers):
    """
    [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers for GET).
    For public APIs like Petstore, authentication is typically not enforced on this endpoint.
    This test verifies that the endpoint does not return 401/403 even with invalid auth headers,
    indicating it's publicly accessible or auth is not configured.
    """
    order_id = 7  # Use a valid ID for the request
    url = f"{api_base_url}/store/order/{order_id}"
    invalid_auth_headers = headers.copy()
    invalid_auth_headers["Authorization"] = "Bearer invalid_token_12345"
    invalid_auth_headers["api_key"] = "invalid_api_key"

    response = requests.get(url, headers=invalid_auth_headers)

    # For a public API, it should succeed (200) or fail for other reasons (e.g., 404 if order not found),
    # but not due to authentication issues (401/403).
    assert response.status_code not in [401, 403], \
        f"Expected not to receive 401/403, but got {response.status_code}. Auth might be enforced."

    # Further assertion to ensure the test itself is not broken by other factors
    assert response.status_code in [200, 404], \
        f"Unexpected status code {response.status_code} received when simulating unauthorized GET."

# --- DELETE /store/order/{orderId} Tests ---

def test_delete_order_by_id_200_positive(api_base_url, headers):
    """
    [Positive] 200 OK with successful deletion for DELETE /store/order/{orderId}.
    Note: For public APIs, order existence can vary. We will attempt to delete orderId=1.
    If orderId=1 does not exist, this test will fail expecting 200 but receiving 404.
    If it succeeds (200), subsequent GETs for orderId=1 should yield 404.
    """
    order_id_to_delete = 1 # A valid ID for deletion. This might return 404 if it doesn't exist.
    url = f"{api_base_url}/store/order/{order_id_to_delete}"
    response = requests.delete(url, headers=headers)

    assert response.status_code == 200, \
        f"Expected status code 200 for deletion, got {response.status_code}. " \
        f"Order {order_id_to_delete} might not exist or already be deleted."

    # Validate response structure for successful deletion (if provided by API)
    # Petstore usually returns a standard APIResponse object on successful delete
    delete_response = response.json()
    assert isinstance(delete_response, dict), "Delete response payload is not a dictionary"
    assert "code" in delete_response and isinstance(delete_response["code"], int)
    assert "type" in delete_response and isinstance(delete_response["type"], str)
    assert "message" in delete_response and isinstance(delete_response["message"], str)
    assert str(order_id_to_delete) in delete_response["message"], "Deletion message does not mention the deleted ID"

    # Optional: Verify the order is indeed deleted by attempting to GET it
    get_response = requests.get(url, headers=headers)
    assert get_response.status_code == 404, \
        f"Expected 404 after deleting order {order_id_to_delete}, but got {get_response.status_code}."

@pytest.mark.parametrize("order_id, expected_status, description", [
    (0, 400, "Order ID below minimum (0) for DELETE"),
    (-1, 400, "Negative Order ID (-1) for DELETE"),
    ("invalid", 400, "Non-integer Order ID (string) for DELETE"),
    ("!@#", 400, "Special characters as Order ID for DELETE"),
    ("", 404, "Empty string as Order ID for DELETE (malformed URL)"),
    ("10000000000000000000", 400, "Very large integer (out of range/overflow) for DELETE")
])
def test_delete_order_by_id_negative_invalid_input_boundary(api_base_url, headers, order_id, expected_status, description):
    """
    [Negative] 400/404 Invalid input/Boundary testing for DELETE /store/order/{orderId}.
    Covers out-of-range IDs, wrong data types, and malformed inputs.
    """
    url = f"{api_base_url}/store/order/{order_id}" if order_id != "" else f"{api_base_url}/store/order/"
    response = requests.delete(url, headers=headers)

    assert response.status_code == expected_status, \
        f"{description}: Expected status code {expected_status}, got {response.status_code} for orderId='{order_id}'"

    # Basic check for error message if 400
    if response.status_code == 400:
        assert isinstance(response.json(), dict), "Error response is not a dictionary"
        assert "message" in response.json() or "type" in response.json(), "Error message or type missing"

def test_delete_order_by_id_security_unauthorized(api_base_url, headers):
    """
    [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers for DELETE).
    Similar to GET, this verifies that DELETE endpoint does not return 401/403 with invalid auth headers.
    """
    order_id_for_security_test = 99999 # Use a non-existent ID to avoid actual deletion in security test
    url = f"{api_base_url}/store/order/{order_id_for_security_test}"
    invalid_auth_headers = headers.copy()
    invalid_auth_headers["Authorization"] = "Bearer invalid_token_delete_123"
    invalid_auth_headers["api_key"] = "invalid_delete_api_key"

    response = requests.delete(url, headers=invalid_auth_headers)

    assert response.status_code not in [401, 403], \
        f"Expected not to receive 401/403, but got {response.status_code}. Auth might be enforced for DELETE."

    # For a non-existent order with invalid auth, typically expects 404 (Order not found)
    assert response.status_code == 404, \
        f"Unexpected status code {response.status_code} received when simulating unauthorized DELETE for non-existent order."