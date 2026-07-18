from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import InteractionRequest, InteractionResponse
from services.llm_service import ask_gemini_json
from services.memory_service import get_user_health_context
from services.openfda_service import check_drug_interaction
from auth_utils import get_optional_user
from database import get_connection
import json

router = APIRouter()


@router.post("/check", response_model=InteractionResponse)
async def check_interactions(
    req: InteractionRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    if len(req.medicines) < 2:
        raise HTTPException(status_code=400, detail="At least 2 medicines required")

    user_id = str(current_user.get("user_id", "")) if current_user else ""
    user_context = get_user_health_context(user_id) if user_id else ""

    # Check OpenFDA for each pair
    openfda_results = {}
    medicines = req.medicines
    for i in range(len(medicines)):
        for j in range(i + 1, len(medicines)):
            key = f"{medicines[i]}_{medicines[j]}"
            openfda_results[key] = check_drug_interaction(medicines[i], medicines[j])

    patient_profile_section = ""
    if user_context:
        patient_profile_section = f"""
PATIENT PROFILE:
{user_context}

Also check if any of these medicines conflict with the patient's existing chronic_conditions or allergies.
Add this as an additional interaction in your response if relevant.
"""

    prompt = f"""
You are a clinical pharmacist AI. Check interactions between these medicines:
{json.dumps(req.medicines)}

OpenFDA adverse event reports found:
{json.dumps(openfda_results)}

{patient_profile_section}

Respond with this exact JSON structure:
{{
  "risk_level": "Safe" or "Moderate" or "Dangerous",
  "interactions": [
    {{
      "drug_a": "First medicine name",
      "drug_b": "Second medicine name",
      "risk": "Mild" or "Moderate" or "Dangerous",
      "explanation": "Plain language explanation in {req.language}",
      "recommendation": "What the patient should do in {req.language}"
    }}
  ]
}}

Rules:
- explanation and recommendation MUST be in the {req.language} language.
- Only include pairs that actually have interactions
- If no interactions found, return empty interactions array and risk_level "Safe"
- risk_level is the highest risk among all pairs
- Be specific and medically accurate
- Keep explanations clear for non-medical users
"""
    try:
        result = ask_gemini_json(prompt)

        conn = get_connection()
        conn.execute(
            "INSERT INTO drug_interactions (medicines, risk_level, result_json) VALUES (?,?,?)",
            (json.dumps(req.medicines), result.get("risk_level", "Safe"), json.dumps(result))
        )
        conn.commit()
        conn.close()

        return InteractionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
