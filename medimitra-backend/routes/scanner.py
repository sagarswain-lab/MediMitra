from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import ScannerRequest, ScannerResponse, ScannerDetails
from services.llm_service import ask_gemini_json
from services.memory_service import get_user_health_context
from services.openfda_service import verify_medicine
from auth_utils import get_optional_user
from database import get_connection
import json

router = APIRouter()


@router.post("/verify", response_model=ScannerResponse)
async def verify_medicine_scan(
    req: ScannerRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    user_id = str(current_user.get("user_id", "")) if current_user else ""
    user_context = get_user_health_context(user_id) if user_id else ""

    openfda_data = {}
    if req.medicine_name:
        openfda_data = verify_medicine(req.medicine_name)

    patient_profile_section = ""
    if user_context:
        patient_profile_section = f"""
PATIENT PROFILE:
{user_context}

After the standard authenticity check, add a field "suitability" to the response:
- Check if this medicine's active ingredients conflict with the patient's known allergies or conditions
- Return one of:
  "✅ Suitable for your health profile"
  "⚠️ Caution: May not suit your profile — [reason]"
  "❌ Not recommended: You are allergic to [ingredient]"
"""
    else:
        patient_profile_section = """For the "suitability" field, return: "ℹ️ Log in and set up your health profile for personalized suitability check" """

    prompt = f"""
You are a pharmaceutical verification AI. Respond ONLY in {req.language}.

Medicine name provided by user: "{req.medicine_name or 'Not provided'}"
OpenFDA verification result: {json.dumps(openfda_data)}

{patient_profile_section}

Analyze this medicine and respond with this exact JSON structure:
{{
  "safety_score": integer between 0 and 100,
  "verdict": "Genuine" or "Suspicious" or "Counterfeit",
  "details": {{
    "drug_name": "Full medicine name with dosage",
    "manufacturer": "Manufacturer name in {req.language}",
    "batch_number": "Realistic batch number like SP-2024-789",
    "expiry": "Expiry date in {req.language}",
    "openfda_status": "Verified" or "Not Found"
  }},
  "actions": [
    "Action step 1 in {req.language}",
    "Action step 2 in {req.language}",
    "Action step 3 in {req.language}"
  ],
  "suitability": "Suitability assessment string as described above"
}}

Rules:
- Translate all medicine-related fields and advice to {req.language}.
- If OpenFDA verified is true → safety_score 80-95, verdict Genuine
- If OpenFDA not found → safety_score 45-65, verdict Suspicious
- actions should match the verdict (reassuring if genuine, cautionary if suspicious)
- Always include 3 action steps
"""
    try:
        result = ask_gemini_json(prompt)

        conn = get_connection()
        conn.execute(
            "INSERT INTO medicine_scans (medicine_name, safety_score, verdict, result_json) VALUES (?,?,?,?)",
            (req.medicine_name, result.get("safety_score", 0), result.get("verdict", ""), json.dumps(result))
        )
        conn.commit()
        conn.close()

        return ScannerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
