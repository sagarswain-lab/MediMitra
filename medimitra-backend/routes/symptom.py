from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from typing import Optional
from models.schemas import SymptomRequest, SymptomResponse, SymptomPdfRequest
from services.llm_service import ask_gemini_json, stream_llm
from services.memory_service import add_memory, get_relevant_memories, get_user_health_context
from auth_utils import get_optional_user
from database import get_connection
import json
import io

router = APIRouter()


@router.post("/check", response_model=SymptomResponse)
async def check_symptoms(
    req: SymptomRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    # Determine user_id from JWT (preferred) or request body
    user_id = None
    if current_user:
        user_id = str(current_user.get("user_id", ""))
    elif req.user_id:
        user_id = req.user_id

    # ── Fetch patient health context ──
    user_context = get_user_health_context(user_id) if user_id else ""

    # ── Mem0: fetch relevant past symptom history ──
    memory_context = ""
    if user_id:
        memories = get_relevant_memories(user_id=user_id, query=req.symptoms, limit=5)
        if memories:
            memory_context = (
                "\n\nRelevant patient history from previous visits:\n"
                + "\n".join(f"- {m}" for m in memories)
                + "\n\nTake this history into account when analysing current symptoms.\n"
            )

    profile_section = ""
    if user_context:
        profile_section = f"""
IMPORTANT PATIENT PROFILE — USE THIS TO PERSONALIZE YOUR RESPONSE:
{user_context}

Consider the patient's allergies and conditions when suggesting home remedies. Never suggest remedies that conflict with their known allergies or conditions.
If patient has a chronic condition that worsens these symptoms, highlight that clearly.
"""

    prompt = f"""\
You are a medical AI assistant. A user has described their symptoms.

Symptoms: {req.symptoms}
Duration: {req.duration}
Severity (1-10): {req.severity}
{memory_context}{profile_section}
Analyze these symptoms and respond with this exact JSON structure:
{{
  "condition": "Most likely condition name",
  "severity": "Mild" or "Moderate" or "Severe",
  "confidence": integer between 60 and 95,
  "explanation": "2-3 sentence plain language explanation of what this condition is",
  "home_remedies": ["remedy 1", "remedy 2", "remedy 3", "remedy 4"],
  "red_flags": ["warning sign 1", "warning sign 2", "warning sign 3"]
}}

Rules:
- Be helpful but always recommend consulting a doctor
- home_remedies must have exactly 4 items
- red_flags must have exactly 3 items
- severity is based on the combination of symptoms and severity score
- confidence reflects how closely symptoms match the condition
- Respond entirely in {req.language} language
- If language is not English, translate all text including condition name, explanation, remedies and red flags to {req.language}
"""
    try:
        result = ask_gemini_json(prompt)

        # ── Save to database ──
        conn = get_connection()
        conn.execute(
            "INSERT INTO symptom_checks (symptoms, duration, severity, condition, result_json) VALUES (?,?,?,?,?)",
            (req.symptoms, req.duration, req.severity, result.get("condition", ""), json.dumps(result)),
        )
        conn.commit()
        conn.close()

        # ── Mem0: store a memory of this symptom check ──
        if user_id:
            summary = (
                f"Patient reported: {req.symptoms}. "
                f"Duration: {req.duration}, severity {req.severity}/10. "
                f"AI suggested condition: {result.get('condition', 'unknown')} "
                f"({result.get('severity', 'unknown')} severity, "
                f"{result.get('confidence', 0)}% confidence)."
            )
            add_memory(
                user_id=user_id,
                content=summary,
                metadata={"type": "symptom_check", "condition": result.get("condition", "")},
            )

        return SymptomResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── SSE Streaming endpoint ──
@router.post("/stream")
async def stream_symptoms(
    req: SymptomRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Server-Sent Events endpoint for the symptom checker.
    Streams AI tokens as they arrive so the user sees text immediately.
    Final event: data: [DONE] <json_payload>\n\n
    """
    user_id = None
    if current_user:
        user_id = str(current_user.get("user_id", ""))
    elif req.user_id:
        user_id = req.user_id

    user_context = get_user_health_context(user_id) if user_id else ""

    memory_context = ""
    if user_id:
        memories = get_relevant_memories(user_id=user_id, query=req.symptoms, limit=5)
        if memories:
            memory_context = (
                "\n\nRelevant patient history from previous visits:\n"
                + "\n".join(f"- {m}" for m in memories)
                + "\n\nTake this history into account when analysing current symptoms.\n"
            )

    profile_section = ""
    if user_context:
        profile_section = f"""
IMPORTANT PATIENT PROFILE — USE THIS TO PERSONALIZE YOUR RESPONSE:
{user_context}

Consider the patient's allergies and conditions when suggesting home remedies. Never suggest remedies that conflict with their known allergies or conditions.
If patient has a chronic condition that worsens these symptoms, highlight that clearly.
"""

    prompt = f"""\
You are a medical AI assistant. A user has described their symptoms.

Symptoms: {req.symptoms}
Duration: {req.duration}
Severity (1-10): {req.severity}
{memory_context}{profile_section}
Analyze these symptoms and respond with this exact JSON structure:
{{
  "condition": "Most likely condition name",
  "severity": "Mild" or "Moderate" or "Severe",
  "confidence": integer between 60 and 95,
  "explanation": "2-3 sentence plain language explanation",
  "home_remedies": ["remedy 1", "remedy 2", "remedy 3", "remedy 4"],
  "red_flags": ["warning sign 1", "warning sign 2", "warning sign 3"]
}}

Rules:
- Be helpful but always recommend consulting a doctor
- home_remedies must have exactly 4 items
- red_flags must have exactly 3 items
- Respond entirely in {req.language} language
- IMPORTANT: Respond with valid JSON only. No markdown, no backticks, no extra text.
"""

    import re as _re

    async def event_generator():
        buffer = ""
        try:
            for chunk in stream_llm(prompt):
                buffer += chunk
                safe = chunk.replace("\n", "\\n")
                yield f"data: {safe}\n\n"

            clean = buffer.strip()
            clean = _re.sub(r"```json\s*", "", clean)
            clean = _re.sub(r"```\s*", "", clean).strip()
            try:
                result = json.loads(clean)
            except Exception:
                result = {"error": "Could not parse AI response", "raw": buffer[:500]}

            try:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO symptom_checks (symptoms, duration, severity, condition, result_json) "
                    "VALUES (?,?,?,?,?)",
                    (req.symptoms, req.duration, req.severity,
                     result.get("condition", ""), json.dumps(result)),
                )
                conn.commit()
                conn.close()
            except Exception as db_err:
                print(f"[stream] DB save error: {db_err}")

            if user_id and "condition" in result:
                summary = (
                    f"Patient reported: {req.symptoms}. "
                    f"Duration: {req.duration}, severity {req.severity}/10. "
                    f"AI suggested: {result.get('condition','unknown')} "
                    f"({result.get('severity','unknown')} severity, "
                    f"{result.get('confidence',0)}% confidence)."
                )
                try:
                    add_memory(
                        user_id=user_id,
                        content=summary,
                        metadata={"type": "symptom_check", "condition": result.get("condition", "")},
                    )
                except Exception as mem_err:
                    print(f"[stream] Mem0 save error: {mem_err}")

            yield f"data: [DONE] {json.dumps(result)}\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── PDF download endpoint ──
@router.post("/download-pdf")
async def download_symptom_pdf(req: SymptomPdfRequest):
    """Generate and stream a branded PDF for a symptom check result."""
    try:
        from services.pdf_service import generate_symptom_pdf
        pdf_bytes = generate_symptom_pdf(req.dict())
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="symptom_report.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
