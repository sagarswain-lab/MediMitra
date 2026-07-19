"""Quick test to verify Gemini vision API with key rotation."""
import sys, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from services.llm_service import ask_gemini_vision

# 1x1 white PNG - properly padded base64
test_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAABjE+ibYAAAAASUVORK5CYII="

print("Testing Gemini vision with 3-key rotation and gemini-2.5-flash...")
try:
    result = ask_gemini_vision(
        'What is in this image? Reply with JSON only: {"color": "your answer"}',
        test_img
    )
    print("Result:", result)
    print("\nOK - Gemini vision is working!")
except Exception as e:
    print(f"\nFAIL - Error: {e}")

