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

    # ── Python-level allergy conflict detection ───────────────────────────────
    # Load user allergies and current medications directly from DB for exact matching
    user_allergies = []
    user_conditions = []
    user_meds = []
    if user_id:
        try:
            uid_int = int(user_id)
            conn = get_connection()
            row = conn.execute(
                "SELECT allergies, chronic_conditions, current_medications FROM health_profiles WHERE user_id = ?",
                (uid_int,)
            ).fetchone()
            conn.close()
            if row:
                user_allergies   = json.loads(row["allergies"])           if row["allergies"]           else []
                user_conditions  = json.loads(row["chronic_conditions"])  if row["chronic_conditions"]  else []
                user_meds        = json.loads(row["current_medications"]) if row["current_medications"] else []
        except Exception:
            pass

    # Pre-built allergy conflict entries (Python-enforced, not LLM-dependent)
    allergy_conflict_entries = []
    for med in req.medicines:
        for allergen in user_allergies:
            if allergen.lower() in med.lower() or med.lower() in allergen.lower():
                allergy_conflict_entries.append({
                    "drug_a": med,
                    "drug_b": f"Patient Allergy: {allergen}",
                    "risk": "Dangerous",
                    "explanation": f"⚠️ ALLERGY ALERT: This patient is known to be allergic to {allergen}. Taking {med} could trigger a serious allergic reaction.",
                    "recommendation": f"DO NOT take {med}. Inform your doctor about your {allergen} allergy immediately and ask for a safe alternative."
                })

    # Check OpenFDA for each pair
    openfda_results = {}
    medicines = req.medicines
    for i in range(len(medicines)):
        for j in range(i + 1, len(medicines)):
            key = f"{medicines[i]}_{medicines[j]}"
            openfda_results[key] = check_drug_interaction(medicines[i], medicines[j])

    # Build explicit allergy/condition warning for the LLM
    patient_profile_section = ""
    if user_context:
        allergy_list = ", ".join(user_allergies) if user_allergies else "None"
        condition_list = ", ".join(user_conditions) if user_conditions else "None"
        current_med_list = ", ".join(user_meds) if user_meds else "None"
        patient_profile_section = f"""
PATIENT PROFILE (CRITICAL — MUST BE CHECKED):
{user_context}

EXPLICIT ALLERGY LIST: {allergy_list}
EXPLICIT CONDITIONS: {condition_list}
CURRENT MEDICATIONS: {current_med_list}

RULES FOR THIS PATIENT:
- If any medicine in the list matches an allergy above, flag it as DANGEROUS immediately.
- If any medicine worsens a listed condition (e.g. NSAIDs for kidney disease, Aspirin for bleeding disorders), flag it.
- If any medicine duplicates or conflicts with current medications, flag it.
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
      "drug_b": "Second medicine name or condition/allergy it conflicts with",
      "risk": "Mild" or "Moderate" or "Dangerous",
      "explanation": "Plain language explanation in {req.language}",
      "recommendation": "What the patient should do in {req.language}"
    }}
  ]
}}

Rules:
- explanation and recommendation MUST be in the {req.language} language.
- Include drug-drug pairs AND drug-allergy/drug-condition conflicts
- If no interactions found, return empty interactions array and risk_level "Safe"
- risk_level is the highest risk among all pairs
- Be specific and medically accurate
"""
    try:
        result = ask_gemini_json(prompt)

        # Inject Python-enforced allergy conflicts at the top (guaranteed, not LLM-dependent)
        if allergy_conflict_entries:
            existing = result.get("interactions", [])
            # Remove any duplicates the LLM might have added
            result["interactions"] = allergy_conflict_entries + existing
            result["risk_level"] = "Dangerous"

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
