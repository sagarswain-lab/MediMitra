from fastapi import APIRouter, HTTPException
from models.schemas import SeasonalRequest, SeasonalResponse
from services.llm_service import ask_gemini_json

router = APIRouter()

def get_season(month: int) -> tuple:
    if 6 <= month <= 9:
        return "Monsoon", "monsoon"
    elif month <= 2 or month >= 11:
        return "Winter", "winter"
    else:
        return "Summer", "summer"

@router.post("/alerts", response_model=SeasonalResponse)
async def get_seasonal_alerts(req: SeasonalRequest):
    season_name, season_css = get_season(req.month)

    prompt = f"""
AI Public Health India - Season: {season_name}, Month: {req.month}, Loc: {req.latitude}, {req.longitude}.
Language: {req.language} (Respond ONLY in this language).

JSON result:
{{
  "season": "{season_name}",
  "alert": "Main alert with emoji",
  "season_css": "{season_css}",
  "diseases": [
    {{ "name": "...", "risk": "High/Med/Low", "symptoms": ["...", "..."], "prevention": "..." }}
  ],
  "dos": ["...", "...", "...", "...", "..."],
  "donts": ["...", "...", "...", "..."],
  "diet_tips": ["...", "...", "...", "..."]
}}
- 3 diseases, 5 dos, 4 donts, 4 diet tips.
- Indian focus. Use {req.language} for all fields, including the "season" name and "alert" text.
- If language is not English, translate everything.
"""
    try:
        result = ask_gemini_json(prompt)
        return SeasonalResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))