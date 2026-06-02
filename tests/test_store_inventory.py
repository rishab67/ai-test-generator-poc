import pytest
import requests
import json

BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = "/store/inventory"
FULL_URL = f"{BASE_URL}{ENDPOINT}"

API_KEY_HEADER_NAME = "api_key"

def test_get_inventory_200_ok():
    """
    [Positive] Test case 1: Retrieve inventory successfully with a 200 OK status.
    Verifies the response structure against the OpenAPI schema:
    an object where keys are strings (status codes) and values are integers (quantities).
    """
    response = requests.get(FULL_URL)

    assert response.status_code == 200, \
        f"Expected status 200, but got {response.status_code}. Response: {response.text}"
    assert response.headers["Content-Type"].startswith("application/json"), \
        f"Expected Content-Type 'application/json', but got {response.headers.get('Content-Type')}"

    inventory_data = response.json()
    assert isinstance(inventory_data, dict), \
        f"Response payload should be a dictionary, but got {type(inventory_data)}"
    assert len(inventory_data) > 0, \
        "Inventory dictionary should not be empty for a successful operation."

    for key, value in inventory_data.items():
        assert isinstance(key, str), \
            f"Inventory key '{key}' (type: {type(key)}) should be a string."
        assert isinstance(value, int), \
            f"Inventory value for key '{key}' (value: {value}, type: {type(value)}) should be an integer."
        assert value >= 0, \
            f"Inventory quantity for key '{key}' should be non-negative, but got {value}."

def test_get_inventory_400_405_invalid_input_with_body():
    """
    [Negative] Test case 2: Invalid input - sending a request body with a GET request.
    GET requests are generally not expected to have a body. Sending one should ideally
    result in a 400 Bad Request or 405 Method Not Allowed.
    """
    invalid_body_payload = {"status": "available", "quantity": 10, "extra_field": "test"}
    headers = {"Content-Type": "application/json"}
    
    response = requests.get(FULL_URL, headers=headers, json=invalid_body_payload)

    if response.status_code in [400, 405]:
        assert True 
    else:
        assert response.status_code == 200, \
            f"Expected status 400 or 405 for GET with body, but got {response.status_code}. Response: {response.text}"
        
        inventory_data = response.json()
        assert isinstance(inventory_data, dict)
        for key, value in inventory_data.items():
            assert isinstance(key, str) and isinstance(value, int)
        
        pytest.fail(f"API returned 200 OK for GET with an unexpected request body. "
                     "This might indicate lenient server behavior or a deviation from strict HTTP method semantics. "
                     f"Expected 400/405. Response: {response.text}")

def test_get_inventory_400_405_boundary_testing_query_params():
    """
    [Negative] Test case 3: Boundary testing with unexpected or invalid query parameters.
    The /store/inventory GET endpoint has no defined parameters. This tests robustness
    by sending arbitrary, boundary-value, or type-mismatched query parameters.
    """
    boundary_test_params = [
        {"key": "nonExistentParam", "value": "someValue"},
        {"key": "id", "value": "notAnInteger"},
        {"key": "empty", "value": ""},
        {"key": "negVal", "value": "-1"},
        {"key": "longString", "value": "a" * 2000}
    ]

    for test_param in boundary_test_params:
        params = {test_param["key"]: test_param["value"]}
        response = requests.get(FULL_URL, params=params)

        assert response.status_code == 200, \
            f"Expected status 200 for GET with unexpected query param '{test_param['key']}={test_param['value']}', " \
            f"but got {response.status_code}. Response: {response.text}"
        
        inventory_data = response.json()
        assert isinstance(inventory_data, dict), \
            f"Response payload should be a dictionary for query '{test_param['key']}={test_param['value']}'"
        for key, value in inventory_data.items():
            assert isinstance(key, str) and isinstance(value, int)

def test_get_inventory_401_403_security_missing_api_key():
    """
    [Security] Test case 4a: Unauthorized - Simulate missing authentication header.
    The OpenAPI schema explicitly lists 'api_key' security for this endpoint.
    This test verifies that omitting the required API key results in a 401 Unauthorized or 403 Forbidden.
    """
    response = requests.get(FULL_URL)

    if response.status_code in [401, 403]:
        assert True
    else:
        assert response.status_code == 200, \
            f"Expected status 401 or 403 for missing API key, but got {response.status_code}. Response: {response.text}"
        
        inventory_data = response.json()
        assert isinstance(inventory_data, dict)
        for key, value in inventory_data.items():
            assert isinstance(key, str) and isinstance(value, int)
        
        pytest.fail(f"API returned 200 OK for GET without an API key, despite the schema requiring it. "
                     "This represents a potential security finding (unsecured access) or a schema-implementation discrepancy. "
                     f"Expected 401/403. Response: {response.text}")

def test_get_inventory_401_403_security_invalid_api_key():
    """
    [Security] Test case 4b: Unauthorized - Simulate invalid authentication header.
    Tests if providing an invalid API key results in a 401 Unauthorized or 403 Forbidden status.
    """
    invalid_api_key = "INVALID_API_KEY_TEST_STRING_1234567890"
    headers = {API_KEY_HEADER_NAME: invalid_api_key}

    response = requests.get(FULL_URL, headers=headers)

    if response.status_code in [401, 403]:
        assert True
    else:
        assert response.status_code == 200, \
            f"Expected status 401 or 403 for invalid API key, but got {response.status_code}. Response: {response.text}"
        
        inventory_data = response.json()
        assert isinstance(inventory_data, dict)
        for key, value in inventory_data.items():
            assert isinstance(key, str) and isinstance(value, int)
        
        pytest.fail(f"API returned 200 OK for GET with an invalid API key, despite the schema requiring security. "
                     "This represents a potential security finding (invalid key still grants access) or a schema-implementation discrepancy. "
                     f"Expected 401/403. Response: {response.text}")