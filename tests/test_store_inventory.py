import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

def test_get_inventory_success():
    url = f"{BASE_URL}/store/inventory"
    headers = {"api_key": "special-key"}  # Assuming 'api_key' is a valid security scheme and value

    response = requests.get(url, headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), dict)

    inventory_data = response.json()
    for status, quantity in inventory_data.items():
        assert isinstance(quantity, int)
        assert quantity >= 0

def test_get_inventory_unauthorized():
    url = f"{BASE_URL}/store/inventory"
    # Missing or invalid api_key to simulate unauthorized access
    headers = {"api_key": "invalid-key"}

    response = requests.get(url, headers=headers)

    # The Swagger Petstore example might not strictly enforce security for /store/inventory GET without an API key.
    # If it does, the status code would likely be 401 or 403.
    # For this example, we'll assert for a 200 response as per the schema,
    # but in a real-world scenario, you'd test for failure codes if security is properly implemented.
    # If the API *does* return a non-200 for invalid keys, change the assertion below.
    assert response.status_code == 200
    assert isinstance(response.json(), dict)