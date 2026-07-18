from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import PrescriptionRequest, PrescriptionResponse
from services.llm_service import ask_gemini_vision
from services.memory_service import get_user_health_context
from auth_utils import get_optional_user
from database import get_connection
import json
import base64

router = APIRouter()


@router.post("/read", response_model=PrescriptionResponse)
async def read_prescription(
    req: PrescriptionRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = str(current_user.get("user_id", "")) if current_user else ""
    user_context = get_user_health_context(user_id) if user_id else ""

    patient_profile_section = ""
    if user_context:
        patient_profile_section = f"""
PATIENT PROFILE:
{user_context}

For each medicine extracted:
- Check if the patient is ALLERGIC to this medicine or its ingredients based on their known allergies
- Check if this medicine CONFLICTS with their chronic conditions (e.g. avoid NSAIDs for kidney patients)
- Check if this medicine INTERACTS with their current_medications list
- Add a field "patient_warning" to each medicine object:
  - If conflict found: "⚠️ WARNING: You may be allergic to this medicine or it conflicts with your conditions. Consult doctor before taking."
  - If no conflict: "✅ No known conflicts with your profile"
"""
    else:
        patient_profile_section = """For the "patient_warning" field, return empty string "" as no patient profile is available."""

    prompt = f"""
You are a medical AI assistant specialized in reading doctor prescriptions.
Analyze the attached image.

GUIDELINES:
1. If the image IS NOT a medical prescription (e.g., a photo of a leaf, a person, or generic object), respond with "medicines": [] and an explanation in {req.language} like "The uploaded image does not appear to be a medical prescription. Please upload a clear photo of your prescription."
2. If it IS a prescription, extract ALL medicine names, dosages, and instructions.
3. For each medicine, explain in plain language (in {req.language}) what it is, what it treats, and common side effects.

{patient_profile_section}

Respond with this exact JSON structure:
{{
  "medicines": [
    {{
      "name": "Medicine name with strength",
      "dosage": "e.g. 1 tablet / 5ml",
      "frequency": "e.g. Twice daily / Every 8 hours",
      "duration": "e.g. 7 days / Finish course",
      "timing": "e.g. After meals / Empty stomach",
      "what_it_is": "Simple explanation in {req.language}",
      "what_it_treats": "Simple explanation in {req.language}",
      "side_effects": "Common warnings in {req.language}",
      "patient_warning": "Patient-specific warning or empty string"
    }}
  ],
  "explanation": "Summarized overview of instructions in {req.language}",
  "translated_text": "Brief clinical summary in {req.language}"
}}
"""
    try:
        result = ask_gemini_vision(prompt, req.image_base64)

        conn = get_connection()
        conn.execute(
            "INSERT INTO prescription_reads (language, result_json) VALUES (?,?)",
            (req.language, json.dumps(result))
        )
        conn.commit()
        conn.close()

        return PrescriptionResponse(**result)
    except Exception as e:
        print(f"Prescription parsing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
