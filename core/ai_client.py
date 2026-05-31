import os
from google import genai
from pyee import cls


class AITestGenerator:
    def __init__(self):
        # This looks for the API_KEY variable in your environment
        self.client = genai.Client(api_key=os.getenv("API_KEY"))
        self.model_name = "gemini-2.5-flash-lite"

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
        - Use the `requests` library (we will migrate to Playwright API later).
        - Include rich Pytest assertions for status codes and response structures.
        - Do NOT output any explanations, markdown formatting, or conversational text. Return ONLY pure, executable Python code.
        """
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text