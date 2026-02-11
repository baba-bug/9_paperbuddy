import google.generativeai as genai
import os
import sys

# Use the key provided by the user
API_KEY = 'AIzaSyC6nkwM8qSlIR1PJhho1LLFrStTCCDGJ1A'

print(f"google-generativeai version: {genai.__version__}")

genai.configure(api_key=API_KEY)

try:
    with open("models_list.txt", "w", encoding="utf-8") as f:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
    print("Models listed successfully to models_list.txt")
except Exception as e:
    print(f"Error: {e}")
