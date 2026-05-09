import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing Gemini API with key: {api_key[:8]}...")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    response = model.generate_content("Hello, are you there?")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
