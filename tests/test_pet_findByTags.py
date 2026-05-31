import pytest
import requests

BASE_URL = "https://petstore.swagger.io/v2"

def test_find_pets_by_tags_success_single_tag():
    params = {"tags": "dog"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 200
    pets = response.json()
    assert isinstance(pets, list)
    if pets:
        assert all("tags" in pet and "dog" in [tag["name"] for tag in pet["tags"]] for pet in pets)

def test_find_pets_by_tags_success_multiple_tags():
    params = {"tags": "dog,friendly"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 200
    pets = response.json()
    assert isinstance(pets, list)
    if pets:
        assert all("tags" in pet and all(tag["name"] in ["dog", "friendly"] for tag in pet["tags"]) for pet in pets)

def test_find_pets_by_tags_no_pets_found():
    params = {"tags": "nonexistent_tag"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 200
    pets = response.json()
    assert isinstance(pets, list)
    assert len(pets) == 0

def test_find_pets_by_tags_empty_tags_parameter():
    params = {"tags": ""}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 400

def test_find_pets_by_tags_missing_tags_parameter():
    response = requests.get(f"{BASE_URL}/pet/findByTags")
    assert response.status_code == 400

def test_find_pets_by_tags_deprecated_endpoint():
    params = {"tags": "cat"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 200
    assert 'deprecated' in response.request.headers.get('Deprecated', '')

def test_find_pets_by_tags_response_schema():
    params = {"tags": "dog"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params)
    assert response.status_code == 200
    pets = response.json()
    for pet in pets:
        assert "id" in pet
        assert "name" in pet
        assert "category" in pet
        assert "photoUrls" in pet
        assert "tags" in pet
        assert "status" in pet
        assert isinstance(pet["id"], int)
        assert isinstance(pet["name"], str)
        assert isinstance(pet["category"], dict)
        assert isinstance(pet["photoUrls"], list)
        assert isinstance(pet["tags"], list)
        assert isinstance(pet["status"], str)

def test_find_pets_by_tags_accept_header_json():
    params = {"tags": "dog"}
    headers = {"Accept": "application/json"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params, headers=headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")

def test_find_pets_by_tags_accept_header_xml():
    params = {"tags": "dog"}
    headers = {"Accept": "application/xml"}
    response = requests.get(f"{BASE_URL}/pet/findByTags", params=params, headers=headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")