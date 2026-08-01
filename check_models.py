import os
from google import genai
from dotenv import load_dotenv

# Load your API key
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 Asking Google for valid model names...")

try:
    # Fetch the list of available models for your specific key/region
    models = client.models.list()
    for m in models:
        # Print the exact string the API expects
        print(m.name)
        
except Exception as e:
    print(f"❌ Error fetching models: {e}")