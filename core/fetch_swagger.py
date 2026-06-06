import requests

# 1. Fetch the raw menu from the internet
response = requests.get("https://petstore.swagger.io/v2/swagger.json")

# 2. Convert the raw text into an organized Python dictionary (The Cabinet)
swagger_data = response.json()

# 3. Go to the "paths" drawer and grab all the endpoint names (The Keys)
endpoint_drawer = swagger_data["paths"]
all_endpoints = endpoint_drawer.keys()

# 4. Print the list of endpoints so we can see them cleanly
print("--- CLEAN LIST OF ENTERPRISE ENDPOINTS ---")
for endpoint in all_endpoints:
    print(endpoint)