from fastapi import APIRouter, HTTPException
from models.schemas import LifestyleRequest, LifestyleResponse
from services.gemini_service import ask_gemini_json
from database import get_connection
import json

router = APIRouter()

@router.post("/plan", response_model=LifestyleResponse)
async def generate_lifestyle_plan(req: LifestyleRequest):
    bmi = round(req.weight / ((req.height / 100) ** 2), 1)

    prompt = f"""
Health Advisor - Age: {req.age}, BMI: {bmi}, Goal: {req.goal}, Activity: {req.activity}, Diet: {req.diet}.
Conditions: {', '.join(req.conditions) if req.conditions else 'None'}.
Language: {req.language} (Respond ONLY in this language).

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

        # Save to database
        conn = get_connection()
        conn.execute(
            "INSERT INTO lifestyle_plans (age, goal, activity, bmi, result_json) VALUES (?,?,?,?,?)",
            (req.age, req.goal, req.activity, bmi, json.dumps(result))
        )
        conn.commit()
        conn.close()

        return LifestyleResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))