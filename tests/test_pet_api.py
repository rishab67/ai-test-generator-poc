import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

def test_add_new_pet_success():
    payload = {
        "name": "Buddy",
        "status": "available"
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Buddy"
    assert response_data["status"] == "available"

def test_add_new_pet_invalid_input_missing_name():
    payload = {
        "status": "available"
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 405

def test_add_new_pet_invalid_input_missing_status():
    payload = {
        "name": "Buddy"
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 405

def test_add_new_pet_invalid_input_empty_payload():
    payload = {}
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 405

def test_add_new_pet_invalid_input_non_string_name():
    payload = {
        "name": 123,
        "status": "available"
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 405

def test_add_new_pet_invalid_input_non_string_status():
    payload = {
        "name": "Buddy",
        "status": 123
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 405

def test_add_new_pet_idempotency():
    payload1 = {
        "name": "UniqueBuddy",
        "status": "pending"
    }
    response1 = requests.post(f"{BASE_URL}/pet", json=payload1)
    assert response1.status_code == 200
    pet_id = response1.json()["id"]

    payload2 = {
        "name": "UniqueBuddy",
        "status": "pending"
    }
    response2 = requests.post(f"{BASE_URL}/pet", json=payload2)
    assert response2.status_code == 200
    assert response2.json()["id"] == pet_id

    # Clean up the created pet
    requests.delete(f"{BASE_URL}/pet/{pet_id}")

def test_add_new_pet_different_status_values():
    valid_statuses = ["available", "pending", "sold"]
    for status_value in valid_statuses:
        payload = {
            "name": f"PetWithStatus{status_value.capitalize()}",
            "status": status_value
        }
        response = requests.post(f"{BASE_URL}/pet", json=payload)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == f"PetWithStatus{status_value.capitalize()}"
        assert response_data["status"] == status_value
        requests.delete(f"{BASE_URL}/pet/{response_data['id']}")

def test_add_new_pet_long_name():
    long_name = "a" * 255
    payload = {
        "name": long_name,
        "status": "available"
    }
    response = requests.post(f"{BASE_URL}/pet", json=payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == long_name
    assert response_data["status"] == "available"
    requests.delete(f"{BASE_URL}/pet/{response_data['id']}")