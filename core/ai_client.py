import os
from google import genai


class AITestGenerator:
    def __init__(self):
        # 1. The Locksmith
        self.client = genai.Client(api_key=os.getenv("API_KEY"))

        # 2. The Two Batteries (Added the missing comma!)
        self.available_models = [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash"
        ]

        self.current_index = 0

        # 3. The Active Battery (Fixed the variable name!)
        self.active_model = self.available_models[self.current_index]

    def swap_model(self):
        """The Switch: Flips between model 0 and model 1."""

        # Removed the word 'Change' to make it valid Python syntax
        if self.current_index == 0:
            self.current_index = 1
        else:
            self.current_index = 0

        self.active_model = self.available_models[self.current_index]

        print(f"🔄 Swapped AI Model! Now using: {self.active_model}")
        return self.active_model

    def generate_api_test(self, endpoint_path: str, schema_data: dict):
        prompt = f"""
        You are a Principal API SDET and Security Tester.
        Write a highly comprehensive Pytest script for the endpoint: {endpoint_path}
        Use this OpenAPI schema: {schema_data}

        You MUST generate the following test cases:
        1. [Positive] 200 OK with a perfect, complete payload.
        2. [Negative] 400/405 Invalid input (missing required fields).
        3. [Negative] 400/405 Boundary testing (e.g., sending an integer when a string is expected, or an empty string).
        4. [Security] 401/403 Unauthorized (simulate missing or invalid authentication headers if applicable).

        STRICT RULES:
        - The BASE_URL must be hardcoded as: "https://petstore.swagger.io/v2"
        - Use the `requests` library.
        - Include rich Pytest assertions for status codes and response structures.
        - Do NOT output any explanations, markdown formatting, or conversational text. Return ONLY pure, executable Python code.
        """
        response = self.client.models.generate_content(
            model=self.active_model,
            contents=prompt,
        )
        return response.text