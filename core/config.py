import os
from dotenv import load_dotenv

# 1. Load the .env file
load_dotenv()

# 2. Fetch the key
api_key = os.getenv("API_KEY")

# 3. ENTERPRISE VALIDATION: Fail fast with a clear error
if api_key is None:
    raise ValueError("CRITICAL ERROR: API_KEY was not found! Check your .env file name and location.")

