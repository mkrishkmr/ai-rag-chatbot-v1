import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("No GOOGLE_API_KEY found in .env")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("Available Embedding Models:")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
