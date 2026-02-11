import google.generativeai as genai
import os

# Use the key from the file (I will copy it here for the test script since I can't easily import it without side effects if I didn't structure it as a module)
API_KEY = 'AIzaSyC6nkwM8qSlIR1PJhho1LLFrStTCCDGJ1A'

genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
