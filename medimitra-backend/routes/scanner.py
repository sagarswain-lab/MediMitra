from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import ScannerRequest, ScannerResponse, ScannerDetails
from services.llm_service import ask_gemini_json, ask_gemini_vision
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

    # ── Image analysis: extract medicine info from the uploaded image ──
    image_context = ""
    detected_name = req.medicine_name or ""
    if req.image_base64:
        try:
            img_prompt = f"""
            You are a pharmaceutical expert. Look at this medicine packaging image carefully.

            Extract the following information:
            1. Medicine name (with strength/dosage if visible, e.g. "Paracetamol 500mg")
            2. Manufacturer name
            3. Batch number
            4. Expiry date
            5. Any other text visible on the packaging

            Also check:
            - Does the packaging look professional and genuine?
            - Are there any signs of tampering, poor printing, or suspicious elements?

            Respond ONLY in English with this JSON:
            {{"medicine_name": "...", "manufacturer": "...", "batch_number": "...", "expiry": "...",
              "packaging_quality": "Good/Poor/Suspicious", "visible_text": "brief summary of all visible text",
              "suspicious_signs": "None or description of issues"}}
            """
            img_result = ask_gemini_vision(img_prompt, req.image_base64)
            detected_name = img_result.get("medicine_name") or detected_name or "Unknown Medicine"
            image_context = f"""
            IMAGE ANALYSIS RESULT:
            - Medicine Name (from image): {img_result.get('medicine_name', 'Not readable')}
            - Manufacturer (from image): {img_result.get('manufacturer', 'Not readable')}
            - Batch Number (from image): {img_result.get('batch_number', 'Not readable')}
            - Expiry Date (from image): {img_result.get('expiry', 'Not readable')}
            - Packaging Quality: {img_result.get('packaging_quality', 'Unknown')}
            - Visible Text: {img_result.get('visible_text', '')}
            - Suspicious Signs: {img_result.get('suspicious_signs', 'None')}
            """
        except Exception as img_err:
            print(f"[Scanner] Image analysis failed (non-fatal): {img_err}")
            image_context = "Image analysis was not available."

    # ── OpenFDA lookup ──
    openfda_data = {}
    if detected_name:
        openfda_data = verify_medicine(detected_name)

    prompt = f"""
    You are a pharmaceutical verification AI. Respond ONLY in {req.language}.

    Medicine name provided by user: "{req.medicine_name or 'Not provided'}"
    {image_context}
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
    - If OpenFDA not found but packaging looks Good → safety_score 55-70, verdict Suspicious
    - If packaging is Poor or Suspicious or has suspicious signs → safety_score 20-45, verdict Suspicious/Counterfeit
    - actions should match the verdict (reassuring if genuine, cautionary if suspicious)
    - Use information from the IMAGE ANALYSIS to fill in details where available
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
