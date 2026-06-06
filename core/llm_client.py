from google import genai
import config


class GeminiTestGenerator:
    def __init__(self):
        # We pass the secure API key directly into the modern client
        self.client = genai.Client(api_key=config.api_key)

        # We use the fastest, free-tier model available
        self.model_name = "gemini-2.5-flash-lite"

    def test_connection(self):
        print("Sending message to Gemini...")

        # This tells the client to generate a response
        response = self.client.models.generate_content(
            model=self.model_name,
            contents="Hello AI! You are now connected to my local machine. Say 'Connection Successful' if you can hear me."
        )
        print("AI Response:", response.text)

    def generate_api_test(self, api_contract: str):
        print("Generating test code...")

        # 1. The Prompt Engineering Layer: Forcing the AI to be an SDET
        system_rules = """
                You are an expert Python SDET writing scripts for an enterprise Playwright API test framework. 
                Write a complete pytest script for the dynamic API contract provided below. 

                CRITICAL STRUCTURAL RULES:
                1. Only return the raw Python code, no markdown formatting.
                2. DO NOT include any fixtures (like `@pytest.fixture`) inside this file. Assume `api_request_context` is provided globally.
                3. Every test function MUST accept `api_request_context` as its first argument.
                4. DO NOT import or use `expect()` from playwright.sync_api. Use standard Python `assert`.

                DYNAMIC DATA RULES:
                5. DYNAMIC PATHS: If the endpoint contains variables (e.g., {user_id}), pass those variables dynamically into the URL string using python f-strings.
                6. HEADERS: If the contract specifies headers, pass them explicitly using the `headers={...}` parameter inside the Playwright request method (e.g., api_request_context.get(url, headers={...})).
                """

        # 2. Combine the rules with the user's API details
        full_prompt = f"{system_rules}\n\nAPI Contract:\n{api_contract}"

        # Step A: Write the code to call self.client.models.generate_content() here.
        # Hint: Look at how you did it in test_connection, but this time pass `full_prompt` into the contents= parameter!
        response = self.client.models.generate_content(
            model = self.model_name,
            contents=full_prompt,
        )
        # Step B: Return the response.text
        return response.text



# This block runs the test when you execute the file
if __name__ == "__main__":
    ai = GeminiTestGenerator()

    # We feed it a fake API contract
    fake_api = "POST /api/users. Requires JSON body with 'name' and 'role'."

    # Call your new function and print the result
    generated_code = ai.generate_api_test(fake_api)
    print("\n--- GENERATED CODE ---\n")
    print(generated_code)