import os
from llm_client import GeminiTestGenerator


def create_test_file():
    # 1. Initialize your engine
    ai = GeminiTestGenerator()

    # 2. Define the API contract
    # We feed the AI a complex, dynamic contract
    api_contract = """
        ENDPOINT: GET /api/v1/projects/{project_id}/tasks
        HEADERS: 
          - Authorization: Bearer mock_token_123
          - X-Client-ID: Automation_Suite
        QUERY PARAMETERS:
          - status: completed
        EXPECTED RESPONSE:
          - Status: 200 OK
          - Body: JSON array of tasks containing 'task_id' and 'title'.
        """
    # 3. Get the code from the AI
    generated_code = ai.generate_api_test(api_contract)

    # 4. Clean the output (LLMs sometimes wrap code in Markdown like ```python ... ```)
    clean_code = generated_code.replace("```python", "").replace("```", "").strip()

    # 5. Define where to save it
    file_name = "../tests/test_generated_api.py"

    print(f"Writing test to {file_name}...")

    # YOUR TURN: Write the Python code to save the 'clean_code' string into a file named 'file_name'.
    # Hint: Use Python's built-in `with open(...)` pattern.
    with open(file_name, "w") as f:
        f.write(clean_code)
    print("Test generation complete! You can now run 'pytest test_generated_api.py'")


if __name__ == "__main__":
    create_test_file()