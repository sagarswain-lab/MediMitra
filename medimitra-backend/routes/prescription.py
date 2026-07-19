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
You are a medical AI assistant specialized in reading doctor prescriptions, INCLUDING HANDWRITTEN ones.
Analyze the attached image carefully.

IMPORTANT INSTRUCTIONS:
1. This may be a HANDWRITTEN prescription - read carefully even if text is unclear
2. Look for medicine names written by hand in both English and local languages
3. Extract ANY readable medicine names, even if partially legible
4. If you can read even 1-2 medicines, extract them - don't return empty list
5. Common medicine names to look for: Paracetamol, Diclofenac, Omeprazole, Amoxicillin, etc.

GUIDELINES:
1. If the image IS NOT a medical prescription at all (e.g., a photo of nature, person, or random object), respond with "medicines": [] and explanation in {req.language}.
2. If it IS a prescription (even handwritten/unclear), extract ALL readable medicine names, dosages, and instructions.
3. For medicines where dosage is unclear, use "As directed by doctor"
4. For each medicine, explain in plain language (in {req.language}) what it is, what it treats, and common side effects.

{patient_profile_section}

Respond with this exact JSON structure:
{{
  "medicines": [
    {{
      "name": "Medicine name with strength (extract even if partially readable)",
      "dosage": "e.g. 1 tablet / 5ml or 'As directed'",
      "frequency": "e.g. Twice daily / Every 8 hours or 'As directed'",
      "duration": "e.g. 7 days / Finish course or 'As directed'",
      "timing": "e.g. After meals / Empty stomach or 'As directed'",
      "what_it_is": "Simple explanation in {req.language}",
      "what_it_treats": "Simple explanation in {req.language}",
      "side_effects": "Common warnings in {req.language}",
      "patient_warning": "Patient-specific warning or empty string"
    }}
  ],
  "explanation": "Summarized overview in {req.language}. If handwritten and partially unclear, mention that.",
  "translated_text": "Brief clinical summary in {req.language}"
}}

CRITICAL: If you can see ANY medicine names at all (even 1-2 medicines), extract them. Only return empty medicines list if the image is clearly NOT a prescription.
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
