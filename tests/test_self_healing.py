import pytest
import requests
import os
from google import genai

BASE_URL = "https://petstore.swagger.io/v2"


def test_pet_schema_self_healing():
    """
    An API test that intentionally fails to demonstrate Self-Healing.
    """
    # 1. We make a standard API call
    response = requests.get(f"{BASE_URL}/pet/findByStatus?status=available")
    data = response.json()

    first_pet = data[0]

    try:
        # 2. THE TRAP: We assert a key that DOES NOT EXIST anymore.
        # We pretend the developer changed the API schema, and our old test is looking for 'pet_category_name'
        assert "pet_category_name" in first_pet, "Key 'pet_category_name' is missing from the response!"

    except AssertionError as e:
        # 3. THE HEALER: The test caught its own failure!
        print(f"\n[🚨 TEST FAILED] Assertion Error: {e}")
        print("[🔧 SELF-HEALING] Initiating AI Diagnostics...")

        # Now we ask the AI to fix our broken test
        api_key = os.environ.get("API_KEY")
        client = genai.Client(api_key=api_key)

        prompt = f"""
        You are an AI Self-Healing engine for a Pytest framework.
        My test just failed. 

        Here is the error: {e}
        Here is the actual JSON response I got from the server: {first_pet}

        Analyze the actual JSON response. The developer clearly changed the key names.
        What is the correct key name I should be asserting instead of 'pet_category_name'? 
        Write a short explanation, and provide the exact Python assertion code I should use to fix my script.
        """

        ai_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        print("\n" + "=" * 50)
        print("🤖 AI DIAGNOSTIC & FIX")
        print("=" * 50)
        print(ai_response.text)
        print("=" * 50)

        # We re-raise the error so the test still technically fails in the CI/CD pipeline,
        # but now the developer has the exact fix printed in the logs!
        raise e