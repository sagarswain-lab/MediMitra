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

    # Load allergies directly from DB for explicit banned-food enforcement
    user_allergies = []
    user_conditions = []
    if user_id:
        try:
            uid_int = int(user_id)
            conn = get_connection()
            row = conn.execute(
                "SELECT allergies, chronic_conditions FROM health_profiles WHERE user_id = ?",
                (uid_int,)
            ).fetchone()
            conn.close()
            if row:
                user_allergies  = json.loads(row["allergies"])          if row["allergies"]          else []
                user_conditions = json.loads(row["chronic_conditions"]) if row["chronic_conditions"] else []
        except Exception:
            pass

    patient_profile_section = ""
    if user_context:
        # Build a banned foods list from actual allergies
        banned_foods_lines = []
        for allergen in user_allergies:
            al = allergen.lower()
            if "peanut" in al or "groundnut" in al:
                banned_foods_lines.append(f"- {allergen} (includes peanut butter, groundnuts, mixed nuts with peanuts)")
            elif "milk" in al or "dairy" in al or "lactose" in al:
                banned_foods_lines.append(f"- {allergen} (includes milk, cheese, butter, yoghurt, cream, whey)")
            elif "gluten" in al or "wheat" in al:
                banned_foods_lines.append(f"- {allergen} (includes bread, wheat flour, pasta, chapati)")
            else:
                banned_foods_lines.append(f"- {allergen}")

        banned_block = "\n".join(banned_foods_lines) if banned_foods_lines else "- None"

        patient_profile_section = f"""
PATIENT PROFILE — STRICTLY FOLLOW THIS:
{user_context}

══════════════════════════════════════════════
🚫 BANNED FOODS — PATIENT IS ALLERGIC TO THESE:
{banned_block}
⚠️  NEVER include these in ANY meal, snack, drink, or ingredient list across all 7 days.
══════════════════════════════════════════════

ADDITIONAL RULES:
- NEVER suggest foods that worsen their chronic conditions
  (e.g. no sugary foods for Diabetics, no salty foods for High BP patients)
- ALWAYS consider their current medications (e.g. avoid Vitamin K rich foods if on Warfarin)
- Tailor exercise intensity to their conditions
  (e.g. low impact for Heart patients, no high intensity for Asthma patients)
- Start the plan with: "Personalized for [Name] — conditions: [list or None]"
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
