import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

@pytest.fixture
def user_payload():
    return [
        {
            "id": 101,
            "username": "testuser1",
            "firstName": "Test",
            "lastName": "UserOne",
            "email": "testuser1@example.com",
            "password": "password123",
            "phone": "123-456-7890",
            "userStatus": 1
        },
        {
            "id": 102,
            "username": "testuser2",
            "firstName": "Test",
            "lastName": "UserTwo",
            "email": "testuser2@example.com",
            "password": "password456",
            "phone": "098-765-4321",
            "userStatus": 0
        }
    ]

def test_create_users_with_array_success(user_payload):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=user_payload, headers=headers)
    assert response.status_code == 200

def test_create_users_with_array_empty_payload():
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=[], headers=headers)
    assert response.status_code == 200

def test_create_users_with_array_invalid_payload_type():
    headers = {'Content-Type': 'application/json'}
    invalid_payload = {"user": "not_an_array"}
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=invalid_payload, headers=headers)
    assert response.status_code != 200 # Expecting a client error for invalid payload structure

def test_create_users_with_array_missing_required_fields():
    headers = {'Content-Type': 'application/json'}
    payload_missing_id = [
        {
            "username": "testuser_no_id",
            "firstName": "Test",
            "lastName": "NoID",
            "email": "testnouser@example.com",
            "password": "passwordabc",
            "phone": "555-555-5555",
            "userStatus": 1
        }
    ]
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=payload_missing_id, headers=headers)
    assert response.status_code != 200 # Expecting a client error if 'id' is truly mandatory for creation in the backend

def test_create_users_with_array_duplicate_user_id():
    headers = {'Content-Type': 'application/json'}
    payload_duplicate_id = [
        {
            "id": 200,
            "username": "duplicate_id_user1",
            "firstName": "Dup",
            "lastName": "One",
            "email": "dup1@example.com",
            "password": "pwd1",
            "phone": "111-111-1111",
            "userStatus": 1
        },
        {
            "id": 200,
            "username": "duplicate_id_user2",
            "firstName": "Dup",
            "lastName": "Two",
            "email": "dup2@example.com",
            "password": "pwd2",
            "phone": "222-222-2222",
            "userStatus": 1
        }
    ]
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=payload_duplicate_id, headers=headers)
    # The behavior for duplicate IDs in an array creation is often implementation-specific.
    # It might create the first one and error on the second, or error entirely.
    # We'll assert it's not a success code if the backend enforces uniqueness.
    assert response.status_code != 200

def test_create_users_with_array_with_existing_user():
    # First, create a user to ensure it exists
    user_to_pre_create = {
        "id": 300,
        "username": "pre_existing_user",
        "firstName": "Pre",
        "lastName": "Existing",
        "email": "pre@example.com",
        "password": "password_pre",
        "phone": "333-333-3333",
        "userStatus": 1
    }
    headers = {'Content-Type': 'application/json'}
    create_response = requests.post(f"{BASE_URL}/user", json=user_to_pre_create, headers=headers)
    assert create_response.status_code == 200

    # Now try to create a list including the pre-existing user and a new one
    payload_with_existing = [
        user_to_pre_create, # This user already exists
        {
            "id": 301,
            "username": "new_user_in_array",
            "firstName": "New",
            "lastName": "InArray",
            "email": "newinarray@example.com",
            "password": "password_new",
            "phone": "444-444-4444",
            "userStatus": 0
        }
    ]
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=payload_with_existing, headers=headers)
    # Again, the behavior is implementation-dependent. It might update, ignore, or error.
    # A strict interpretation might expect an error if the primary key constraint is violated.
    assert response.status_code != 200 # Assuming the backend enforces uniqueness and rejects duplicates.

def test_create_users_with_array_large_payload():
    headers = {'Content-Type': 'application/json'}
    large_payload = []
    for i in range(100):
        large_payload.append({
            "id": 400 + i,
            "username": f"largeuser_{i}",
            "firstName": "Large",
            "lastName": f"User_{i}",
            "email": f"largeuser{i}@example.com",
            "password": f"pwd_large_{i}",
            "phone": f"555-{i:03d}-5555",
            "userStatus": i % 2
        })
    response = requests.post(f"{BASE_URL}/user/createWithArray", json=large_payload, headers=headers)
    assert response.status_code == 200