from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import LifestyleRequest, LifestyleResponse, LifestylePdfRequest
from services.llm_service import ask_gemini_json
from database import get_connection
import json
import io

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
    """
    Generate and stream a personalized PDF for a 7-day lifestyle plan.
    """
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