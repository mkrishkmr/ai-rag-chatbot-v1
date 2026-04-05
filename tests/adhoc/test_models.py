import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Listing all available models for your API key...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nAttempting a test generation with 'models/gemini-3-flash-preview'...")
try:
    model = genai.GenerativeModel('gemini-3-flash-preview')
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Failed flash-3: {e}")

print("\nAttempting a test generation with 'models/gemini-3.1-pro-preview'...")
try:
    model = genai.GenerativeModel('gemini-3.1-pro-preview')
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Failed pro-3.1: {e}")
