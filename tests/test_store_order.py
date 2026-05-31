import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

# Helper function to generate a valid order payload
def generate_valid_order_payload():
    return {
        "id": 1,
        "petId": 10,
        "quantity": 1,
        "shipDate": "2024-07-29T10:30:00.000Z",
        "status": "placed",
        "complete": False
    }

# Helper function to generate an invalid order payload (missing required field)
def generate_invalid_order_payload_missing_field():
    return {
        "id": 1,
        "petId": 10,
        "shipDate": "2024-07-29T10:30:00.000Z",
        "status": "placed",
        "complete": False
    }

# Helper function to generate an invalid order payload (incorrect data type)
def generate_invalid_order_payload_incorrect_type():
    return {
        "id": "invalid_id",
        "petId": 10,
        "quantity": 1,
        "shipDate": "2024-07-29T10:30:00.000Z",
        "status": "placed",
        "complete": False
    }

def test_place_order_success():
    """
    Tests successful placement of an order.
    """
    url = f"{BASE_URL}/store/order"
    payload = generate_valid_order_payload()
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data == payload  # Assuming the response echoes the request payload on success
    assert isinstance(response_data, dict)
    assert 'id' in response_data
    assert 'petId' in response_data
    assert 'quantity' in response_data
    assert 'shipDate' in response_data
    assert 'status' in response_data
    assert 'complete' in response_data

def test_place_order_invalid_payload_missing_field():
    """
    Tests placing an order with a missing required field.
    """
    url = f"{BASE_URL}/store/order"
    payload = generate_invalid_order_payload_missing_field()
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)

    assert response.status_code == 400

def test_place_order_invalid_payload_incorrect_type():
    """
    Tests placing an order with an incorrect data type for a field.
    """
    url = f"{BASE_URL}/store/order"
    payload = generate_invalid_order_payload_incorrect_type()
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)

    assert response.status_code == 400

def test_place_order_missing_content_type_header():
    """
    Tests placing an order without the Content-Type header.
    """
    url = f"{BASE_URL}/store/order"
    payload = generate_valid_order_payload()
    headers = {}  # Missing Content-Type

    response = requests.post(url, json=payload, headers=headers)

    # Depending on server implementation, this could be 415 (Unsupported Media Type) or a 400 Bad Request.
    # We'll assert for either common error code.
    assert response.status_code in [400, 415]