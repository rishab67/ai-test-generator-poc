import csv
import os
from google import genai


def read_locust_data(file_path):
    """Opens the Locust CSV file and converts it into a text format."""
    csv_content = ""
    try:
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                csv_content += " | ".join(row) + "\n"
        return csv_content
    except FileNotFoundError:
        return None


def analyze_performance(csv_data):
    """Sends the CSV data to Gemini and asks for an SRE Root Cause Analysis."""
    print("🤖 Waking up the AI Site Reliability Engineer...")

    # 1. Grab the secure API key from your terminal
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("❌ ERROR: API_KEY not found in environment variables.")
        return

    # 2. Initialize the modern Google GenAI Client
    client = genai.Client(api_key=api_key)

    # 3. The 20 LPA System Prompt
    prompt = f"""
    You are a Principal Site Reliability Engineer (SRE). 
    I ran a load test using Locust. Here is the raw CSV output:

    {csv_data}

    Please analyze this data and provide a brief, professional Root Cause Analysis (RCA).
    1. Identify the bottleneck (look closely at the 90th to 99th percentiles).
    2. Explain what a spike in these percentiles usually means in a real-world API.
    3. Give 2 concrete recommendations on how developers can fix it.
    Keep it concise and format it beautifully.
    """

    # 4. Generate the response
    print("📊 Analyzing the metrics (this takes a few seconds)...\n")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    print("=" * 50)
    print("🏆 AI ROOT CAUSE ANALYSIS REPORT")
    print("=" * 50)
    print(response.text)


# --- Main Execution Block ---
if __name__ == "__main__":
    data = read_locust_data("../reports/performance_results_stats.csv")
    if data:
        analyze_performance(data)
    else:
        print("Could not analyze. Missing data.")