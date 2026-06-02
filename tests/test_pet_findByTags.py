import requests
import pytest

BASE_URL = "https://petstore.swagger.io/v2"

# Helper function to validate the structure of a Pet object
def validate_pet_structure(pet):
    assert isinstance(pet, dict), "Pet object must be a dictionary"
    assert "id" in pet and isinstance(pet["id"], int), "Pet must have an 'id' (integer)"
    assert "name" in pet and isinstance(pet["name"], str), "Pet must have a 'name' (string)"
    assert "status" in pet and isinstance(pet["status"], str), "Pet must have a 'status' (string)"

    if "category" in pet:
        assert isinstance(pet["category"], dict), "Category must be a dictionary"
        assert "id" in pet["category"] and isinstance(pet["category"]["id"], int), "Category must have an 'id' (integer)"
        assert "name" in pet["category"] and isinstance(pet["category"]["name"], str), "Category must have a 'name' (string)"

    if "photoUrls" in pet:
        assert isinstance(pet["photoUrls"], list), "Photo URLs must be a list"
        for url in pet["photoUrls"]:
            assert isinstance(url, str), "Each photo URL must be a string"

    if "tags" in pet:
        assert isinstance(pet["tags"], list), "Tags must be a list"
        for tag in pet["tags"]:
            assert isinstance(tag, dict), "Each tag must be a dictionary"
            assert "id" in tag and isinstance(tag["id"], int), "Tag must have an 'id' (integer)"
            assert "name" in tag and isinstance(tag["name"], str), "Tag must have a 'name' (string)"

class TestPetFindByTags:

    ENDPOINT = f"{BASE_URL}/pet/findByTags"

    # 1. [Positive] 200 OK with a perfect, complete payload.
    def test_find_pets_by_tags_positive_200_ok(self):
        """
        Test case for a successful retrieval of pets by existing tags.
        Expects a 200 OK status code and a list of pets conforming to the schema.
        """
        tags_to_find = ["available", "sold"]  # Using common Petstore tags
        params = {"tags": tags_to_find}
        response = requests.get(self.ENDPOINT, params=params)

        assert response.status_code == 200, \
            f"Expected Status Code 200, but got {response.status_code}. Response: {response.text}"
        assert response.headers["Content-Type"].startswith("application/json"), \
            f"Expected Content-Type 'application/json', but got {response.headers['Content-Type']}"

        pets = response.json()
        assert isinstance(pets, list), "Response payload must be a list of pets"

        if pets:
            # If the list is not empty, validate the structure of each pet object
            for pet in pets:
                validate_pet_structure(pet)
        else:
            # An empty list is also a valid successful operation if no pets match the tags
            pass

    # 2. [Negative] 400/405 Invalid input (missing required fields).
    def test_find_pets_by_tags_negative_missing_required_tags(self):
        """
        Test case for missing the required 'tags' query parameter.
        Expects a 400 Bad Request status code according to the OpenAPI schema.
        """
        # Do not provide the 'tags' parameter at all
        response = requests.get(self.ENDPOINT)

        assert response.status_code == 400, \
            f"Expected Status Code 400 for missing 'tags' parameter, but got {response.status_code}. Response: {response.text}"
        assert response.headers["Content-Type"].startswith("application/json") or response.headers["Content-Type"].startswith("application/xml")

        # Check for specific error message in the response body if available
        if response.headers["Content-Type"].startswith("application/json"):
            error_response = response.json()
            assert isinstance(error_response, dict)
            assert error_response.get("message") == "Invalid tag value" or \
                   "Invalid tag value" in response.text

    # 3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
    @pytest.mark.parametrize("invalid_tags_input, expected_status_code", [
        ("", 400),                             # Empty string for the entire 'tags' parameter (?tags=)
        ([], 400),                             # Empty list of tags (requests library will omit the parameter if empty, leading to 400)
        ([""], 400),                           # List containing a single empty string tag (?tags=)
        (["", "available"], 400),              # List containing an empty string tag and a valid tag (?tags=&tags=available)
        ([123], 400),                          # Sending an integer as a tag (API is expected to validate string type)
        (["tag1", "a" * 256], 400),            # Very long tag name (potential boundary for string length)
        (["special-!@#$%", "tag"], 400)        # Tags with special characters if not explicitly allowed
    ])
    def test_find_pets_by_tags_negative_boundary_invalid_tag_values(self, invalid_tags_input, expected_status_code):
        """
        Test cases for various invalid tag inputs and boundary conditions.
        Expects a 400 Bad Request status code as per schema's 'Invalid tag value' response.
        Note: The actual Petstore API might return 200 for some of these, treating them as valid
        strings that simply yield no results. However, adhering strictly to the schema's '400: Invalid tag value'
        description for boundary cases.
        """
        params = {"tags": invalid_tags_input}
        response = requests.get(self.ENDPOINT, params=params)

        assert response.status_code == expected_status_code, \
            f"Expected Status Code {expected_status_code} for invalid tags '{invalid_tags_input}', but got {response.status_code}. Response: {response.text}"
        
        # Verify error message for 400 responses
        if response.status_code == 400:
            if response.headers["Content-Type"].startswith("application/json"):
                error_response = response.json()
                assert isinstance(error_response, dict)
                assert error_response.get("message") == "Invalid tag value" or \
                       "Invalid tag value" in response.text
            elif response.headers["Content-Type"].startswith("application/xml"):
                assert "Invalid tag value" in response.text


    # 4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).
    def test_find_pets_by_tags_security_unauthorized_access(self):
        """
        Test case for unauthorized access, simulating missing authentication credentials.
        The OpenAPI schema indicates 'petstore_auth' security for this endpoint.
        Expects a 401 Unauthorized or 403 Forbidden status code.
        Note: The live Petstore API for findByTags often does not enforce this security
        and might return 200. This test strictly adheres to the schema's security definition.
        """
        tags_to_find = ["available"]
        params = {"tags": tags_to_find}
        # Simulate missing authentication by not providing any headers (e.g., API key, OAuth token)
        response = requests.get(self.ENDPOINT, params=params)

        assert response.status_code in [401, 403], \
            f"Expected Status Code 401 or 403 for unauthorized access, but got {response.status_code}. Response: {response.text}"
        
        # Optionally, check for a generic unauthorized/forbidden message
        if response.status_code == 401:
            assert "Unauthorized" in response.text
        elif response.status_code == 403:
            assert "Forbidden" in response.text