import requests
import pytest
import uuid
import random

BASE_URL = "https://petstore.swagger.io/v2"
PET_ENDPOINT = f"{BASE_URL}/pet"
AUTH_HEADERS = {"api_key": "special-key", "Content-Type": "application/json", "Accept": "application/json"}
UNAUTH_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"} # Headers without API key
INVALID_AUTH_HEADERS = {"api_key": "invalid-key", "Content-Type": "application/json", "Accept": "application/json"}

@pytest.fixture
def pet_payload_base():
    """Fixture to generate a basic pet payload with required fields."""
    return {
        "id": random.randint(100000, 999999),
        "name": f"TestPet-{uuid.uuid4()}",
        "photoUrls": [
            f"http://example.com/photo/{uuid.uuid4()}.jpg"
        ],
        "status": "available"
    }

@pytest.fixture
def pet_payload_complete(pet_payload_base):
    """Fixture to generate a complete pet payload with all optional fields."""
    payload = pet_payload_base.copy()
    payload.update({
        "category": {
            "id": random.randint(1, 100),
            "name": f"Category-{uuid.uuid4().hex[:8]}"
        },
        "tags": [
            {
                "id": random.randint(1, 100),
                "name": f"Tag-{uuid.uuid4().hex[:8]}"
            }
        ]
    })
    return payload

@pytest.fixture
def created_pet_id(pet_payload_complete):
    """Fixture to create a pet and return its ID for update/delete tests. Includes teardown."""
    post_response = requests.post(PET_ENDPOINT, json=pet_payload_complete, headers=AUTH_HEADERS)
    assert post_response.status_code == 200
    pet_id = post_response.json().get("id")
    assert pet_id is not None
    yield pet_id
    # Teardown: Attempt to delete the created pet
    requests.delete(f"{PET_ENDPOINT}/{pet_id}", headers=AUTH_HEADERS)


# --- Test Cases ---

# 1. [Positive] 200 OK with a perfect, complete payload.

def test_post_pet_positive_complete_payload(pet_payload_complete):
    """
    POST /pet: Test adding a new pet with a complete, valid payload, expecting 200 OK.
    """
    response = requests.post(PET_ENDPOINT, json=pet_payload_complete, headers=AUTH_HEADERS)
    assert response.status_code == 200
    response_data = response.json()

    assert isinstance(response_data, dict)
    assert response_data["id"] == pet_payload_complete["id"]
    assert response_data["name"] == pet_payload_complete["name"]
    assert response_data["status"] == pet_payload_complete["status"]
    assert response_data["category"]["id"] == pet_payload_complete["category"]["id"]
    assert response_data["category"]["name"] == pet_payload_complete["category"]["name"]
    assert response_data["photoUrls"] == pet_payload_complete["photoUrls"]
    assert response_data["tags"][0]["id"] == pet_payload_complete["tags"][0]["id"]
    assert response_data["tags"][0]["name"] == pet_payload_complete["tags"][0]["name"]

def test_put_pet_positive_complete_payload(pet_payload_complete):
    """
    PUT /pet: Test updating an existing pet with a complete, valid payload, expecting 200 OK.
    """
    # First, create a pet to ensure it exists for the update
    post_response = requests.post(PET_ENDPOINT, json=pet_payload_complete, headers=AUTH_HEADERS)
    assert post_response.status_code == 200
    created_pet_id = post_response.json().get("id")
    assert created_pet_id is not None

    # Prepare an updated payload
    updated_name = f"UpdatedPet-{uuid.uuid4()}"
    pet_payload_complete["id"] = created_pet_id  # Ensure the ID matches the created pet
    pet_payload_complete["name"] = updated_name
    pet_payload_complete["status"] = "sold"
    pet_payload_complete["category"]["name"] = f"Category-Updated-{uuid.uuid4().hex[:8]}"

    put_response = requests.put(PET_ENDPOINT, json=pet_payload_complete, headers=AUTH_HEADERS)
    assert put_response.status_code == 200
    response_data = put_response.json()

    assert isinstance(response_data, dict)
    assert response_data["id"] == created_pet_id
    assert response_data["name"] == updated_name
    assert response_data["status"] == "sold"
    assert response_data["category"]["name"] == pet_payload_complete["category"]["name"]

    # Clean up the created pet
    requests.delete(f"{PET_ENDPOINT}/{created_pet_id}", headers=AUTH_HEADERS)


# 2. [Negative] 400/405 Invalid input (missing required fields).

@pytest.mark.parametrize("missing_field", ["name", "photoUrls"])
def test_post_pet_negative_missing_required_fields(pet_payload_base, missing_field):
    """
    POST /pet: Test adding a pet with missing required fields (name, photoUrls), expecting 400/405.
    """
    payload = pet_payload_base.copy()
    del payload[missing_field]
    response = requests.post(PET_ENDPOINT, json=payload, headers=AUTH_HEADERS)
    # OpenAPI schema states 405 for 'Invalid input' for POST. 400 is also common for bad requests.
    assert response.status_code in [400, 405]

@pytest.mark.parametrize("missing_field", ["id", "name", "photoUrls"])
def test_put_pet_negative_missing_required_fields(pet_payload_base, created_pet_id, missing_field):
    """
    PUT /pet: Test updating a pet with missing required fields (id, name, photoUrls), expecting 400/405.
    """
    payload = pet_payload_base.copy()
    payload["id"] = created_pet_id  # Ensure a valid ID exists for the update context
    del payload[missing_field]
    response = requests.put(PET_ENDPOINT, json=payload, headers=AUTH_HEADERS)
    # OpenAPI schema states 400 for 'Invalid ID supplied', 405 for 'Validation exception'.
    assert response.status_code in [400, 405]


# 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).

@pytest.mark.parametrize("field, value", [
    ("name", 12345),                       # name as integer (expected string)
    ("name", ""),                          # name as empty string (required)
    ("photoUrls", "not_an_array"),         # photoUrls as string (expected array of strings)
    ("photoUrls", []),                     # photoUrls as empty array (usually requires at least one URL)
    ("status", "invalid_enum_status"),     # status with invalid enum value
    ("id", "not_an_int"),                  # id as string (expected integer)
    ("id", -1)                             # id as negative integer (usually invalid)
])
def test_post_pet_negative_boundary_invalid_types_and_values(pet_payload_base, field, value):
    """
    POST /pet: Test adding a pet with invalid data types or boundary values, expecting 400/405.
    """
    payload = pet_payload_base.copy()
    if field in payload:
        payload[field] = value
    else: # For new fields like category or tags, if they were to be tested for type
        payload[field] = value
    response = requests.post(PET_ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code in [400, 405] # OpenAPI states 405 for 'Invalid input'

@pytest.mark.parametrize("field, value, expected_status_codes", [
    ("id", "not_an_int", [400, 405]),           # id as string (expected integer)
    ("id", 0, [400, 404]),                      # id as 0 (usually not a valid ID, could lead to 404 or 400)
    ("id", -1, [400, 404]),                     # id as negative (usually not a valid ID, could lead to 404 or 400)
    ("name", 12345, [400, 405]),                # name as integer (expected string)
    ("name", "", [400, 405]),                   # name as empty string (required)
    ("photoUrls", "not_an_array", [400, 405]),  # photoUrls as string (expected array)
    ("photoUrls", [], [400, 405]),              # photoUrls as empty array
    ("status", "invalid_enum_status", [400, 405]) # status with invalid enum value
])
def test_put_pet_negative_boundary_invalid_types_and_values(pet_payload_base, created_pet_id, field, value, expected_status_codes):
    """
    PUT /pet: Test updating a pet with invalid data types or boundary values, expecting 400/405/404.
    """
    payload = pet_payload_base.copy()
    payload["id"] = created_pet_id # Start with a valid base ID

    payload[field] = value # Apply the boundary test value to the specified field
    
    response = requests.put(PET_ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code in expected_status_codes # Specific codes per OpenAPI for PUT negatives

def test_put_pet_negative_non_existent_id(pet_payload_base):
    """
    PUT /pet: Test updating a pet with a non-existent ID, expecting 404.
    """
    payload = pet_payload_base.copy()
    payload["id"] = 999999999999999  # A very large, highly likely non-existent ID
    response = requests.put(PET_ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 404 # OpenAPI states 404 for 'Pet not found'


# 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).

def test_post_pet_security_unauthorized_no_headers(pet_payload_complete):
    """
    POST /pet: Test adding a pet without any authentication headers, expecting 401/403.
    """
    response = requests.post(PET_ENDPOINT, json=pet_payload_complete, headers=UNAUTH_HEADERS)
    assert response.status_code in [401, 403]

def test_post_pet_security_unauthorized_invalid_api_key(pet_payload_complete):
    """
    POST /pet: Test adding a pet with an invalid API key, expecting 401/403.
    """
    response = requests.post(PET_ENDPOINT, json=pet_payload_complete, headers=INVALID_AUTH_HEADERS)
    assert response.status_code in [401, 403]

def test_put_pet_security_unauthorized_no_headers(pet_payload_base):
    """
    PUT /pet: Test updating a pet without any authentication headers, expecting 401/403.
    """
    # Create a pet first to have a valid ID to attempt an update on
    post_response = requests.post(PET_ENDPOINT, json=pet_payload_base, headers=AUTH_HEADERS)
    assert post_response.status_code == 200
    created_pet_id = post_response.json().get("id")
    assert created_pet_id is not None

    pet_payload_base["id"] = created_pet_id # Use the created pet's ID
    pet_payload_base["name"] = f"AttemptedUpdate-{uuid.uuid4()}" # Attempt to modify name

    response = requests.put(PET_ENDPOINT, json=pet_payload_base, headers=UNAUTH_HEADERS)
    assert response.status_code in [401, 403]

    # Clean up the created pet
    requests.delete(f"{PET_ENDPOINT}/{created_pet_id}", headers=AUTH_HEADERS)


def test_put_pet_security_unauthorized_invalid_api_key(pet_payload_base):
    """
    PUT /pet: Test updating a pet with an invalid API key, expecting 401/403.
    """
    # Create a pet first to have a valid ID to attempt an update on
    post_response = requests.post(PET_ENDPOINT, json=pet_payload_base, headers=AUTH_HEADERS)
    assert post_response.status_code == 200
    created_pet_id = post_response.json().get("id")
    assert created_pet_id is not None

    pet_payload_base["id"] = created_pet_id # Use the created pet's ID
    pet_payload_base["name"] = f"AttemptedUpdate-{uuid.uuid4()}" # Attempt to modify name

    response = requests.put(PET_ENDPOINT, json=pet_payload_base, headers=INVALID_AUTH_HEADERS)
    assert response.status_code in [401, 403]

    # Clean up the created pet
    requests.delete(f"{PET_ENDPOINT}/{created_pet_id}", headers=AUTH_HEADERS)