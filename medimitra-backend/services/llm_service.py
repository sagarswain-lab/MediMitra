"""
llm_service.py — LLM service layer (now powered by Groq).

Public API is kept identical so no route file needs to change other than the import module name:
  - ask_gemini(prompt)          → str
  - ask_gemini_json(prompt)     → dict
  - ask_gemini_vision(prompt, image_b64) → dict

Groq SDK docs: https://console.groq.com/docs
"""
import os
import json
import re
import time
import base64
from groq import Groq, RateLimitError
from dotenv import load_dotenv

load_dotenv()

# ── Model names ──────────────────────────────────────────────
TEXT_MODEL   = "llama-3.3-70b-versatile"          # fast, powerful text model
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # multimodal / vision

# ── Key rotation ─────────────────────────────────────────────
current_key_index = 0


def _get_current_keys() -> list[str]:
    """Dynamically reload and return the list of API keys from .env."""
    load_dotenv(override=True)
    raw = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or ""
    return [k.strip() for k in raw.split(",") if k.strip()]


def _get_client() -> Groq:
    """Return a Groq client configured with the currently selected key."""
    global current_key_index
    keys = _get_current_keys()
    if not keys:
        raise Exception(
            "No Groq API keys found in .env. Add GROQ_API_KEY=your_key or "
            "GROQ_API_KEYS=key1,key2,... and restart the server."
        )
    key = keys[current_key_index % len(keys)]
    masked = f"...{key[-4:]}" if len(key) > 4 else "***"
    print(f"--- [Groq] Using API Key {current_key_index + 1}/{len(keys)} (ends {masked}) ---")
    return Groq(api_key=key)


def _chat_with_retry(messages: list, model: str, max_retries: int = None) -> str:
    """
    Core retry loop with key rotation on RateLimitError (429).

    Tries each key up to twice before giving up.
    """
    global current_key_index
    keys = _get_current_keys()
    n_keys = len(keys)
    if n_keys == 0:
        raise Exception("No API keys found in .env")

    attempts = n_keys * 2  # try each key twice if needed

    for _ in range(attempts):
        try:
            client = _get_client()
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return completion.choices[0].message.content
        except RateLimitError:
            if n_keys > 1:
                current_key_index = (current_key_index + 1) % n_keys
                print(f"Rate limit hit. Switching to key {current_key_index + 1}/{n_keys}...")
                time.sleep(1)
                continue
            else:
                print("Rate limit hit. Single key — waiting 5 s...")
                time.sleep(5)
                continue
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate" in err or "quota" in err:
                current_key_index = (current_key_index + 1) % max(n_keys, 1)
                print(f"Quota/rate error. Rotating to key {current_key_index + 1}...")
                time.sleep(1)
                continue
            print(f"Groq API error: {e}")
            raise

    raise Exception(
        "All Groq API keys have exceeded their rate limit. "
        "Please add more keys or wait before retrying."
    )


# ── Public API ────────────────────────────────────────────────

def ask_gemini(prompt: str) -> str:
    """Send a text prompt to Groq and return the plain text response."""
    messages = [{"role": "user", "content": prompt}]
    try:
        return _chat_with_retry(messages, model=TEXT_MODEL)
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


def ask_gemini_json(prompt: str) -> dict:
    """Send a text prompt to Groq and return parsed JSON."""
    full_prompt = (
        prompt
        + "\n\nIMPORTANT: Respond with valid JSON only. "
          "No markdown, no backticks, no extra text. Just pure JSON."
    )
    messages = [{"role": "user", "content": full_prompt}]
    try:
        text = _chat_with_retry(messages, model=TEXT_MODEL)
        return _parse_json(text)
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


def ask_gemini_vision(prompt: str, image_b64: str) -> dict:
    """
    Send a text prompt + base64-encoded image to Groq vision model.
    Returns parsed JSON.

    Uses VISION_MODEL (meta-llama/llama-4-scout-17b-16e-instruct) which
    supports multimodal image input via the OpenAI-compatible messages API.
    """
    full_prompt = (
        prompt
        + "\n\nIMPORTANT: Respond with valid JSON only. "
          "No markdown, no backticks, no extra text. Just pure JSON."
    )

    # Build multimodal message: text + inline base64 image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": full_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                    },
                },
            ],
        }
    ]

    try:
        text = _chat_with_retry(messages, model=VISION_MODEL)
        return _parse_json(text)
    except Exception as e:
        raise Exception(f"Groq Vision API error: {str(e)}")


def stream_llm(prompt: str):
    """
    Generator that streams text tokens from Groq as they are produced.

    Yields raw string chunks (not SSE-formatted). The caller (route) is
    responsible for wrapping each chunk in `data: ...\n\n` SSE format.

    Falls back to key rotation on RateLimitError just like _chat_with_retry.
    """
    global current_key_index
    keys = _get_current_keys()
    n_keys = max(len(keys), 1)

    for attempt in range(n_keys * 2):
        try:
            client = _get_client()
            stream = client.chat.completions.create(
                model=TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return  # stream finished cleanly
        except RateLimitError:
            if n_keys > 1:
                current_key_index = (current_key_index + 1) % n_keys
                print(f"[stream_llm] Rate limit — rotating to key {current_key_index + 1}...")
                time.sleep(1)
                continue
            else:
                print("[stream_llm] Rate limit — single key, waiting 5 s...")
                time.sleep(5)
                continue
        except Exception as e:
            print(f"[stream_llm] Error: {e}")
            raise

    raise Exception("All Groq API keys exhausted during streaming.")


def _parse_json(text: str) -> dict:
    """Helper to clean and parse JSON from model response."""
    try:
        text = text.strip()
        # Strip markdown code fences if present
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        if not (text.startswith("{") or text.startswith("[")):
            raise ValueError("Response does not look like JSON")

        return json.loads(text)
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {text}")
        return {"error": "Invalid response format", "raw": text}
