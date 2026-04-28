from fastapi import APIRouter, HTTPException
from models.schemas import SymptomRequest, SymptomResponse
from services.gemini_service import ask_gemini_json
from database import get_connection
import json

router = APIRouter()

@router.post("/check", response_model=SymptomResponse)
async def check_symptoms(req: SymptomRequest):
    prompt = f"""
You are a medical AI assistant. A user has described their symptoms.

Symptoms: {req.symptoms}
Duration: {req.duration}
Severity (1-10): {req.severity}

Analyze these symptoms and respond with this exact JSON structure:
{{
  "condition": "Most likely condition name",
  "severity": "Mild" or "Moderate" or "Severe",
  "confidence": integer between 60 and 95,
  "explanation": "2-3 sentence plain language explanation of what this condition is",
  "home_remedies": ["remedy 1", "remedy 2", "remedy 3", "remedy 4"],
  "red_flags": ["warning sign 1", "warning sign 2", "warning sign 3"]
}}

Rules:
- Be helpful but always recommend consulting a doctor
- home_remedies must have exactly 4 items
- red_flags must have exactly 3 items
- severity is based on the combination of symptoms and severity score
- confidence reflects how closely symptoms match the condition
- Respond entirely in {req.language} language
- If language is not English, translate all text including condition name, explanation, remedies and red flags to {req.language}
"""
    try:
        result = ask_gemini_json(prompt)

        # Save to database
        conn = get_connection()
        conn.execute(
            "INSERT INTO symptom_checks (symptoms, duration, severity, condition, result_json) VALUES (?,?,?,?,?)",
            (req.symptoms, req.duration, req.severity, result.get("condition",""), json.dumps(result))
        )
        conn.commit()
        conn.close()

        return SymptomResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))