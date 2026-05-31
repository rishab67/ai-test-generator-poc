"""
Fetch the live Swagger data.
Select one specific endpoint (we will start with /pet since it's standard).
Instantiate your AITestGenerator class.
Pass the endpoint data to Gemini and print the generated automated test
"""


#_=====================================

import os
import time  # 1. Import the time module to handle our rate limiting
import requests
from dotenv import load_dotenv
from core.ai_client import AITestGenerator
from utils.file_manager import save_generated_test

load_dotenv()


def main():
    print("🚀 STARTING AI BATCH GENERATOR...")

    # 1. Fetch the live Swagger Data
    url = "https://petstore.swagger.io/v2/swagger.json"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Server is down (Status {response.status_code}). Try again later!")
        return

    swagger_data = response.json()
    paths_dictionary = swagger_data["paths"]

    # 2. Fire up the AI client
    ai_engine = AITestGenerator()

    print(f"📦 Found {len(paths_dictionary)} total endpoints. Starting batch generation...\n")

    # 3. THE LOOP: Go through every single endpoint in the Swagger file
    # We use .items() to get both the folder name (endpoint_path) and the contents (schema_data)
    for endpoint_path, schema_data in paths_dictionary.items():
        print(f"⚙️ Processing: {endpoint_path}...")

        # --- CHALLENGE 1: CREATE A SAFE FILENAME ---
        # 1. Remove the first slash so it doesn't start with an underscore
        safe_name = endpoint_path.strip("/")
        # 2. Replace remaining slashes with underscores
        safe_name = safe_name.replace("/", "_")
        # 3. Remove curly braces
        safe_name = safe_name.replace("{", "").replace("}", "")

        # Combine it to make the final python filename!
        final_filename = f"test_{safe_name}.py"

        # --- CHALLENGE 2: GENERATE THE TEST ---
        # Call the ai_engine.generate_api_test method here!
        # Pass in the endpoint_path and the schema_data.
        try:
            generated_code = ai_engine.generate_api_test(
                endpoint_path=endpoint_path,
                schema_data=schema_data
            )
        except Exception as e:
            # If google blocks us, we catch the error, wait for 20 seconds, and retry!
            print(f"Rate Limit hit! Pausing for the 20 seconds before trying...")
            time.sleep(20)


            # Retry the exact same request
            generated_code = ai_engine.generate_api_test(
                endpoint_path =endpoint_path,
                schema_data=schema_data
            )

        # --- CHALLENGE 3: SAVE THE TEST ---
        # Call your save_generated_test function here!
        # Pass in the generated_code and your final_filename.
        save_generated_test(generated_code, final_filename)

        # 4. The Rate Limit Pause (Crucial for free tier)
        print("⏳ Waiting 10 seconds to avoid Gemini Rate Limits...\n")
        time.sleep(10)

    print("🎉 BATCH GENERATION COMPLETE!")


if __name__ == "__main__":
    main()