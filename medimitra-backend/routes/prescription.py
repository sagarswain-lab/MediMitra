from fastapi import APIRouter, HTTPException
from models.schemas import PrescriptionRequest, PrescriptionResponse
from services.llm_service import ask_gemini_vision
from database import get_connection
import json
import base64

router = APIRouter()

@router.post("/read", response_model=PrescriptionResponse)
async def read_prescription(req: PrescriptionRequest):
    prompt = f"""
You are a medical AI assistant specialized in reading doctor prescriptions.
Analyze the attached image.

GUIDELINES:
1. If the image IS NOT a medical prescription (e.g., a photo of a leaf, a person, or generic object), respond with "medicines": [] and an explanation in {req.language} like "The uploaded image does not appear to be a medical prescription. Please upload a clear photo of your prescription."
2. If it IS a prescription, extract ALL medicine names, dosages, and instructions.
3. For each medicine, explain in plain language (in {req.language}) what it is, what it treats, and common side effects.

Respond with this exact JSON structure:
{{
  "medicines": [
    {{
      "name": "Medicine name with strength",
      "dosage": "e.g. 1 tablet / 5ml",
      "frequency": "e.g. Twice daily / Every 8 hours",
      "duration": "e.g. 7 days / Finish course",
      "timing": "e.g. After meals / Empty stomach",
      "what_it_is": "Simple explanation in {req.language}",
      "what_it_treats": "Simple explanation in {req.language}",
      "side_effects": "Common warnings in {req.language}"
    }}
  ],
  "explanation": "Summarized overview of instructions in {req.language}",
  "translated_text": "Brief clinical summary in {req.language}"
}}
"""
    try:
        # Use Vision capability to actually see the image
        result = ask_gemini_vision(prompt, req.image_base64)

        # Save to database
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