"""List all available Gemini models for these API keys."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv(override=True)
raw = os.getenv("GEMINI_API_KEY", "")
keys = [k.strip() for k in raw.split(",") if k.strip()]

for key in keys:
    masked = f"...{key[-4:]}"
    print(f"\n--- Key {masked} ---")
    try:
        genai.configure(api_key=key)
        models = genai.list_models()
        vision_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        for m in vision_models:
            print(f"  {m.name}")
    except Exception as e:
        print(f"  Error: {e}")
