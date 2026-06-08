import os
import time
import pytest
import requests
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

BASE_URL = "https://petstore.swagger.io/v2"


def resilient_ai_call(client, prompt):
    try:
        print("\n[🔄 Routing] Attempt 1: Hitting Primary Server (gemini-3.5-flash)...")
        return client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
    except Exception as e1:
        print(f"⚠️ Primary Failed: {e1}")

    try:
        print("[🔄 Routing] Attempt 2: Hitting Lite Fallback (gemini-3.1-flash-lite)...")
        return client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
    except Exception as e2:
        print(f"⚠️ Lite Fallback Failed: {e2}")

    print("[⏳ Delay] Both nodes congested. Sleeping for 5 seconds...")
    time.sleep(5)

    try:
        print("[🔄 Routing] Final Attempt: Retrying Primary Server (gemini-3.5-flash)...")
        return client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
    except Exception as e3:
        raise Exception(f"All AI nodes exhausted. Final Error: {e3}")


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
        assert "pet_category_name" in first_pet, "Key 'pet_category_name' is missing from the response!"

    except AssertionError as e:
        # 3. THE HEALER: The test caught its own failure!
        print(f"\n[🚨 TEST FAILED] Assertion Error: {e}")
        print("[🔧 SELF-HEALING] Initiating AI Diagnostics...")

        # --- THE SECURE IMPLEMENTATION ---
        api_key = os.getenv("API_KEY")

        if not api_key:
            pytest.fail("❌ SEC EXCEPTION: 'API_KEY' not found in environment. Check your .env file or CI/CD secrets.")

        client = genai.Client(api_key=api_key)
        # ---------------------------------

        prompt = f"""
        I am writing an automated test for an API.
        The test expected the key 'pet_category_name' in this JSON response:
        {first_pet}

        But it failed with this error: {e}

        Analyze the JSON response. What is the correct key related to category or name that I should use instead?
        Provide ONLY the exact Python assertion line of code to fix it. 
        Do not use markdown blocks, just plain text code.
        """

        try:
            # Replaced the raw call with our resilient function
            ai_response = resilient_ai_call(client, prompt)
            print(f"[✅ AI SUGGESTED FIX] Update your code to: {ai_response.text.strip()}")
            pytest.fail("Self-healing diagnosis complete. Please apply the AI fix.")
        except Exception as ai_error:
            pytest.fail(f"❌ AI Diagnostics failed: {ai_error}")