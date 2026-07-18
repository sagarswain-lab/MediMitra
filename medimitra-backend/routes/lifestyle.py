from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from models.schemas import LifestyleRequest, LifestyleResponse, LifestylePdfRequest
from services.llm_service import ask_gemini_json
from services.memory_service import get_user_health_context
from auth_utils import get_optional_user
from database import get_connection
import json
import io

router = APIRouter()


@router.post("/plan", response_model=LifestyleResponse)
async def generate_lifestyle_plan(
    req: LifestyleRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    bmi = round(req.weight / ((req.height / 100) ** 2), 1)

    user_id = str(current_user.get("user_id", "")) if current_user else ""
    user_context = get_user_health_context(user_id) if user_id else ""

    patient_profile_section = ""
    if user_context:
        patient_profile_section = f"""
PATIENT PROFILE — STRICTLY FOLLOW THIS:
{user_context}

CRITICAL RULES for meal planning:
- NEVER suggest foods the patient is allergic to
- NEVER suggest foods that worsen their chronic conditions
  (e.g. no sugary foods for Diabetics, no salty foods for High BP patients, no dairy if lactose intolerant)
- ALWAYS consider their current medications (e.g. avoid Vitamin K rich foods if on Warfarin)
- Tailor exercise intensity to their conditions
  (e.g. low impact for Heart patients, no high intensity for Asthma patients)
- Mention at start of plan: personalized for [conditions]
"""

    prompt = f"""
Health Advisor - Age: {req.age}, BMI: {bmi}, Goal: {req.goal}, Activity: {req.activity}, Diet: {req.diet}.
Conditions: {', '.join(req.conditions) if req.conditions else 'None'}.
Language: {req.language} (Respond ONLY in this language).

{patient_profile_section}

JSON result:
{{
  "bmi": {bmi},
  "plan": [
    {{
      "day": "Monday",
      "morning": {{ "time": "6:30 AM", "drink": "...", "activity": "..." }},
      "meals": {{ "breakfast": "...(kcal)", "snack1": "...", "lunch": "...(kcal)", "snack2": "...", "dinner": "...(kcal)", "total_calories": 1800 }},
      "exercise": {{ "type": "...", "duration": "45 min", "intensity": "...", "routine": ["...", "..."] }},
      "wellness": {{ "water": "...L", "sleep": "...h", "tip": "..." }}
    }}
  ]
}}
- 7 days (Mon-Sun).
- Vary meals/exercise. Match {req.diet} diet & {req.goal} goal.
- Use {req.language} for all text fields, including the names of the days (e.g., Monday should become the {req.language} version).
- Everything must be in {req.language}.
"""
    try:
        result = ask_gemini_json(prompt)

        conn = get_connection()
        conn.execute(
            "INSERT INTO lifestyle_plans (age, goal, activity, bmi, result_json) VALUES (?,?,?,?,?)",
            (req.age, req.goal, req.activity, bmi, json.dumps(result))
        )
        conn.commit()
        conn.close()

        try:
            return LifestyleResponse(**result)
        except Exception as validation_err:
            raise HTTPException(
                status_code=500,
                detail=f"AI response format error: {str(validation_err)}. Raw keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download-pdf")
async def download_lifestyle_pdf(req: LifestylePdfRequest):
    """Generate and stream a personalized PDF for a 7-day lifestyle plan."""
    try:
        from services.pdf_service import generate_lifestyle_pdf
        pdf_bytes = generate_lifestyle_pdf(req.dict())
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="lifestyle_plan.pdf"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
