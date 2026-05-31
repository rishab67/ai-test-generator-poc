import os


def save_generated_test(ai_response_text: str, filename: str):
    """Cleans LLM Markdown and saves the Python string to a file."""

    # 1. The Scissors: Cut away the Markdown formatting
    clean_code = ai_response_text.replace("```python", "").replace("```", "").strip()

    # 2. The Folder: Create a 'tests' directory if it doesn't exist yet
    os.makedirs("tests", exist_ok=True)

    # 3. The Path: Combine the folder and the filename (tests/test_pet_api.py)
    filepath = os.path.join("tests", filename)

    # 4. The Pen: Open the file and write the clean code into it
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(clean_code)

    print(f"✅ SUCCESS: Test script automatically saved to -> {filepath}")