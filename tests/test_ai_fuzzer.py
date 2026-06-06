import pytest
import requests
import os
import json
import time
import re  # NEW: Added Regex module
from google import genai

BASE_URL = "https://petstore.swagger.io/v2"
ENDPOINT = "/pet"


def resilient_ai_call(client, prompt):
    """
    Executes the user's exact fallback strategy:
    1. Try gemini-2.5-flash
    2. Fallback to gemini-2.5-flash-lite
    3. Wait 5 seconds
    4. Try gemini-2.5-flash again
    5. Fail and report error
    """
    # Attempt 1: Primary Model
    try:
        print("\n[🔄 Routing] Attempt 1: Hitting Primary Server (gemini-2.5-flash)...")
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    except Exception as e1:
        print(f"⚠️ Primary Failed: {e1}")

    # Attempt 2: Lite Fallback
    try:
        print("[🔄 Routing] Attempt 2: Hitting Lite Fallback (gemini-2.5-flash-lite)...")
        return client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
    except Exception as e2:
        print(f"⚠️ Lite Fallback Failed: {e2}")

    # Wait for traffic to clear
    print("[⏳ Delay] Both nodes congested. Sleeping for 5 seconds...")
    time.sleep(5)

    # Attempt 3: Final Primary Retry
    try:
        print("[🔄 Routing] Final Attempt: Retrying Primary Server (gemini-2.5-flash)...")
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    except Exception as e3:
        # If it fails here, we explicitly crash the test and return the exact error
        pytest.fail(f"❌ CRITICAL: All AI nodes exhausted. Final Error: {e3}")


@pytest.fixture
def ai_malicious_payload():
    """Asks Gemini to generate an extreme edge-case JSON payload."""
    print("\n[🛡️ AppSec] Generating Structural Fuzzing Payload...")

    api_key = os.environ.get("API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = """
    You are a Senior QA Automation Engineer performing authorized negative boundary testing on a staging API.
    I am testing a POST /pet API endpoint that expects this JSON schema:
    {
      "id": 0,
      "category": { "id": 0, "name": "string" },
      "name": "string",
      "photoUrls": [ "string" ],
      "tags": [ { "id": 0, "name": "string" } ],
      "status": "available"
    }

    Generate a highly complex, boundary-breaking JSON payload to test the server's resilience.
    Include extreme boundary values (like massive integers), incredibly long strings (1000 characters), 
    unexpected data types (like putting arrays where strings should be), and strange unicode characters.

    IMPORTANT: Return ONLY valid JSON format. Do not include markdown tags like ```json. 
    Just the raw JSON dictionary so my Python script can parse it directly.
    ABSOLUTELY NO EXPLANATIONS, NO PREAMBLE, AND NO POSTSCRIPT. ONLY RETURN THE { ... } BLOCK.
    """

    # We now call our custom fault-tolerant function instead of hitting the client directly!
    response = resilient_ai_call(client, prompt)

    if not response or not response.text:
        pytest.fail("❌ The AI refused to answer. We likely tripped a safety filter.")

        # --- NEW REGEX EXTRACTION LOGIC ---
        try:
            # Search for everything between the first { and the last }
            match = re.search(r'\{.*\}', response.text, re.DOTALL)

            if match:
                clean_text = match.group(0)  # Extract just the matched JSON string
                malicious_json = json.loads(clean_text)
                print(f"[🛡️ AppSec] Payload Extracted & Engineered Successfully!")
                return malicious_json
            else:
                pytest.fail(f"❌ Regex could not find any JSON dictionary in the response. Raw: {response.text}")

        except json.JSONDecodeError as e:
            pytest.fail(f"❌ JSON format failed after Regex extraction. Error: {e}\nExtracted Text: {clean_text}")


# --- The Actual Fuzzing Test ---

def test_fuzz_add_pet_endpoint(ai_malicious_payload):
    url = f"{BASE_URL}{ENDPOINT}"

    print(f"\n[💥 Attack] Firing payload at {url}...")
    print("[💥 Attack] Payload size: {} bytes".format(len(json.dumps(ai_malicious_payload))))

    response = requests.post(url, json=ai_malicious_payload)

    print(f"[📊 Result] Server responded with Status Code: {response.status_code}")

    assert response.status_code != 500, \
        f"CRITICAL VULNERABILITY: Server crashed with a 500 error! Response: {response.text}"