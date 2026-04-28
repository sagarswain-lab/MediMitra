import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Model selection - back to flash-latest as requested
MODEL_NAME = "gemini-flash-latest"

# Global index to track which API key we're using
current_key_index = 0

def _get_current_keys():
    """Dynamically reload and return the list of API keys from .env."""
    load_dotenv(override=True)
    raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY")
    if not raw_keys:
        return []
    return [k.strip() for k in raw_keys.split(",") if k.strip()]

def _get_current_model():
    """Configure and return the model with the currently selected API key."""
    keys = _get_current_keys()
    if not keys:
        raise Exception("No Gemini API keys found in .env. Please add GEMINI_API_KEYS=key1,key2...")
    
    # Selection logic with safety for index out of bounds
    key = keys[current_key_index % len(keys)]
    genai.configure(api_key=key)
    
    # Masked log for security but shows it's working
    masked_key = f"...{key[-4:]}" if len(key) > 4 else "***"
    print(f"--- [Gemini] Using API Key {current_key_index + 1}/{len(keys)} (Ending in {masked_key}) ---")
    
    return genai.GenerativeModel(MODEL_NAME)

import time

def _generate_with_retry(prompt, image_part=None, max_retries=None):
    """
    Internal helper to call Gemini with key rotation support.
    Wait logic:
    - On 429: Try the NEXT available API key immediately. 
    - If all keys fail: Wait briefly and retry or fail.
    """
    global current_key_index
    
    # Dynamically fetch current keys
    keys = _get_current_keys()
    keys_to_try = len(keys)
    
    if keys_to_try == 0:
        raise Exception("No API keys found in .env")

    for _ in range(keys_to_try * 2): # Try each key twice if needed
        try:
            model = _get_current_model()
            if image_part:
                response = model.generate_content([prompt, image_part])
            else:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            # If it's a quota/rate limit error (429)
            if "429" in err_str or "quota" in err_str:
                if keys_to_try > 1:
                    # Switch to the next key index
                    current_key_index = (current_key_index + 1) % keys_to_try
                    print(f"Quota reached. Switching to key {current_key_index + 1}/{keys_to_try}...")
                    time.sleep(1) # Small buffer before switching
                    continue 
                else:
                    # If only one key, use the original backoff logic
                    print("Only one API key available. Waiting 5s for reset...")
                    time.sleep(5)
                    continue

            # For other errors, just report and raise
            print(f"Gemini API error: {e}")
            raise e
            
    raise Exception("All Gemini API keys have exceeded their quota. Please add more keys or wait.")

def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response."""
    try:
        return _generate_with_retry(prompt)
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def ask_gemini_json(prompt: str) -> dict:
    """Send a prompt to Gemini and return parsed JSON."""
    try:
        full_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no backticks, no extra text. Just pure JSON."
        text = _generate_with_retry(full_prompt)
        return _parse_json(text)
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def ask_gemini_vision(prompt: str, image_b64: str) -> dict:
    """Send a prompt + image to Gemini and return parsed JSON."""
    try:
        # Prepare the image part
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_b64
        }
        
        full_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no backticks, no extra text. Just pure JSON."
        
        text = _generate_with_retry(full_prompt, image_part=image_part)
        return _parse_json(text)
    except Exception as e:
        raise Exception(f"Gemini Vision API error: {str(e)}")

def _parse_json(text: str) -> dict:
    """Helper to clean and parse JSON from Gemini response."""
    try:
        text = text.strip()
        # Clean markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # If it's empty or doesn't look like JSON, throw
        if not (text.startswith('{') or text.startswith('[')):
             raise Exception("Not JSON")
             
        return json.loads(text)
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {text}")
        return {"error": "Invalid response format", "raw": text}
