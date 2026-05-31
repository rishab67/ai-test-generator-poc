import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

# --- Helper function to create an order ---
def create_order(order_data):
    response = requests.post(f"{BASE_URL}/store/order", json=order_data)
    response.raise_for_status()
    return response.json()

# --- Test cases for GET /store/order/{orderId} ---

def test_get_order_by_valid_id():
    # First, create an order to ensure it exists
    order_payload = {
        "id": 1,
        "petId": 1,
        "quantity": 1,
        "shipDate": "2023-10-27T10:00:00.000Z",
        "complete": False,
        "status": "placed"
    }
    created_order = create_order(order_payload)
    order_id = created_order.get("id")

    response = requests.get(f"{BASE_URL}/store/order/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id
    assert response.json()["petId"] == order_payload["petId"]

def test_get_order_with_id_greater_than_10_should_fail():
    # According to the schema, IDs > 10 will generate exceptions.
    # The specific exception might be a 400 or 404 depending on implementation.
    # We'll test for a common failure code like 400.
    response = requests.get(f"{BASE_URL}/store/order/11")
    # The schema implies an exception, not necessarily a specific status code.
    # We'll check if it's not a 200. A 400 or 404 are likely.
    assert response.status_code != 200

def test_get_order_with_min_valid_id():
    # According to the schema, IDs >= 1 are valid. Test the minimum.
    order_payload = {
        "id": 1,
        "petId": 1,
        "quantity": 1,
        "shipDate": "2023-10-27T10:00:00.000Z",
        "complete": False,
        "status": "placed"
    }
    created_order = create_order(order_payload)
    order_id = created_order.get("id")

    response = requests.get(f"{BASE_URL}/store/order/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

def test_get_order_with_max_valid_id():
    # According to the schema, IDs <= 10 are valid. Test the maximum.
    order_payload = {
        "id": 10,
        "petId": 10,
        "quantity": 1,
        "shipDate": "2023-10-27T10:00:00.000Z",
        "complete": False,
        "status": "placed"
    }
    created_order = create_order(order_payload)
    order_id = created_order.get("id")

    response = requests.get(f"{BASE_URL}/store/order/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

def test_get_nonexistent_order_id():
    # Test with an ID that is unlikely to exist and is within valid range
    response = requests.get(f"{BASE_URL}/store/order/9999")
    assert response.status_code == 404

def test_get_order_with_zero_id():
    # Schema states minimum is 1, so 0 should fail.
    response = requests.get(f"{BASE_URL}/store/order/0")
    assert response.status_code != 200

def test_get_order_with_negative_id():
    # Schema states minimum is 1, so negative should fail.
    response = requests.get(f"{BASE_URL}/store/order/-5")
    assert response.status_code != 200

def test_get_order_with_non_integer_id():
    # Schema states type is integer.
    response = requests.get(f"{BASE_URL}/store/order/abc")
    assert response.status_code == 400 # Expecting a 400 for bad request format

# --- Test cases for DELETE /store/order/{orderId} ---

def test_delete_order_by_valid_id():
    # First, create an order to ensure it exists
    order_payload = {
        "id": 5,
        "petId": 5,
        "quantity": 1,
        "shipDate": "2023-10-27T10:00:00.000Z",
        "complete": False,
        "status": "placed"
    }
    created_order = create_order(order_payload)
    order_id = created_order.get("id")

    delete_response = requests.delete(f"{BASE_URL}/store/order/{order_id}")
    assert delete_response.status_code == 200
    # Verify it's gone by trying to GET it
    get_response = requests.get(f"{BASE_URL}/store/order/{order_id}")
    assert get_response.status_code == 404

def test_delete_nonexistent_order_id():
    # Test deleting an ID that is unlikely to exist and is positive integer
    response = requests.delete(f"{BASE_URL}/store/order/99999")
    assert response.status_code == 404

def test_delete_order_with_positive_integer_id():
    # Schema states positive integer value. Test minimum positive.
    order_payload = {
        "id": 1,
        "petId": 1,
        "quantity": 1,
        "shipDate": "2023-10-27T10:00:00.000Z",
        "complete": False,
        "status": "placed"
    }
    created_order = create_order(order_payload)
    order_id = created_order.get("id")

    delete_response = requests.delete(f"{BASE_URL}/store/order/{order_id}")
    assert delete_response.status_code == 200

def test_delete_order_with_zero_id():
    # Schema states positive integer, so 0 should fail.
    response = requests.delete(f"{BASE_URL}/store/order/0")
    assert response.status_code == 400

def test_delete_order_with_negative_id():
    # Schema states positive integer, so negative should fail.
    response = requests.delete(f"{BASE_URL}/store/order/-10")
    assert response.status_code == 400

def test_delete_order_with_non_integer_id():
    # Schema states type is integer.
    response = requests.delete(f"{BASE_URL}/store/order/xyz")
    assert response.status_code == 400 # Expecting a 400 for bad request format