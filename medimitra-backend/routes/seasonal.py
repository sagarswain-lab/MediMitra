from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import SeasonalRequest, SeasonalResponse
from services.llm_service import ask_gemini_json
from services.memory_service import get_user_health_context
from auth_utils import get_optional_user

router = APIRouter()


def get_season(month: int) -> tuple:
    if 6 <= month <= 9:
        return "Monsoon", "monsoon"
    elif month <= 2 or month >= 11:
        return "Winter", "winter"
    else:
        return "Summer", "summer"


@router.post("/alerts", response_model=SeasonalResponse)
async def get_seasonal_alerts(
    req: SeasonalRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    season_name, season_css = get_season(req.month)

    user_id = str(current_user.get("user_id", "")) if current_user else ""
    user_context = get_user_health_context(user_id) if user_id else ""

    patient_profile_section = ""
    if user_context:
        patient_profile_section = f"""
PATIENT PROFILE:
{user_context}

Personalize the seasonal alerts:
- If patient has respiratory conditions (Asthma, COPD) and it's Winter — add extra respiratory warnings
- If patient is Diabetic and it's Summer — add extra hydration and blood sugar monitoring warnings
- If patient has Heart condition and it's Summer — add heatstroke risk warning prominently
- Mention specific risks relevant to their conditions
"""

    prompt = f"""
AI Public Health India - Season: {season_name}, Month: {req.month}, Loc: {req.latitude}, {req.longitude}.
Language: {req.language} (Respond ONLY in this language).

{patient_profile_section}

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
