from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import SymptomRequest, SymptomResponse, SymptomPdfRequest
from services.llm_service import ask_gemini_json, stream_llm
from services.memory_service import add_memory, get_relevant_memories
from database import get_connection
import json
import io

router = APIRouter()


@router.post("/check", response_model=SymptomResponse)
async def check_symptoms(req: SymptomRequest):
    # ── Mem0: fetch relevant past symptom history for this user ──
    memory_context = ""
    profile_context = ""
    if req.user_id:
        memories = get_relevant_memories(
            user_id=req.user_id,
            query=req.symptoms,
            limit=5,
        )
        if memories:
            memory_context = (
                "\n\nRelevant patient history from previous visits:\n"
                + "\n".join(f"- {m}" for m in memories)
                + "\n\nTake this history into account when analysing current symptoms.\n"
            )
        
        # ── Fetch patient health profile details ──
        conn = get_connection()
        try:
            hp = conn.execute(
                "SELECT age, blood_group, allergies, chronic_conditions, current_medications FROM health_profiles WHERE user_id = ?",
                (req.user_id,)
            ).fetchone()
            if hp:
                hp_age = hp["age"]
                hp_blood = hp["blood_group"]
                hp_allergies = json.loads(hp["allergies"]) if hp["allergies"] else []
                hp_conditions = json.loads(hp["chronic_conditions"]) if hp["chronic_conditions"] else []
                hp_meds = json.loads(hp["current_medications"]) if hp["current_medications"] else []
                
                profile_parts = []
                if hp_age: profile_parts.append(f"Age: {hp_age}")
                if hp_blood: profile_parts.append(f"Blood Group: {hp_blood}")
                if hp_allergies: profile_parts.append(f"Allergies: {', '.join(hp_allergies)}")
                if hp_conditions: profile_parts.append(f"Chronic Conditions: {', '.join(hp_conditions)}")
                if hp_meds: profile_parts.append(f"Current Medications: {', '.join(hp_meds)}")
                
                if profile_parts:
                    profile_context = (
                        "\n\nPatient Health Profile Context:\n"
                        + "\n".join(f"- {part}" for part in profile_parts)
                        + "\n\nTake this health profile (including potential drug allergies/chronic conditions) into account when evaluating symptoms and presenting warnings.\n"
                    )
        finally:
            conn.close()

    prompt = f"""\
You are a medical AI assistant. A user has described their symptoms.

Symptoms: {req.symptoms}
Duration: {req.duration}
Severity (1-10): {req.severity}
{memory_context}{profile_context}
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
        if req.user_id:
            summary = (
                f"Patient reported: {req.symptoms}. "
                f"Duration: {req.duration}, severity {req.severity}/10. "
                f"AI suggested condition: {result.get('condition', 'unknown')} "
                f"({result.get('severity', 'unknown')} severity, "
                f"{result.get('confidence', 0)}% confidence)."
            )
            add_memory(
                user_id=req.user_id,
                content=summary,
                metadata={"type": "symptom_check", "condition": result.get("condition", "")},
            )

        return SymptomResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── SSE Streaming endpoint ──
@router.post("/stream")
async def stream_symptoms(req: SymptomRequest):
    """
    Server-Sent Events endpoint for the symptom checker.
    Streams AI tokens as they arrive so the user sees text immediately.
    Final event: data: [DONE] <json_payload>\n\n
    """
    # Build same context/prompt as /check
    memory_context = ""
    profile_context = ""
    if req.user_id:
        memories = get_relevant_memories(user_id=req.user_id, query=req.symptoms, limit=5)
        if memories:
            memory_context = (
                "\n\nRelevant patient history from previous visits:\n"
                + "\n".join(f"- {m}" for m in memories)
                + "\n\nTake this history into account when analysing current symptoms.\n"
            )
        conn = get_connection()
        try:
            hp = conn.execute(
                "SELECT age, blood_group, allergies, chronic_conditions, current_medications "
                "FROM health_profiles WHERE user_id = ?",
                (req.user_id,)
            ).fetchone()
            if hp:
                hp_allergies  = json.loads(hp["allergies"])           if hp["allergies"]           else []
                hp_conditions = json.loads(hp["chronic_conditions"])  if hp["chronic_conditions"]  else []
                hp_meds       = json.loads(hp["current_medications"]) if hp["current_medications"] else []
                parts = []
                if hp["age"]:        parts.append(f"Age: {hp['age']}")
                if hp["blood_group"]: parts.append(f"Blood Group: {hp['blood_group']}")
                if hp_allergies:     parts.append(f"Allergies: {', '.join(hp_allergies)}")
                if hp_conditions:    parts.append(f"Chronic Conditions: {', '.join(hp_conditions)}")
                if hp_meds:          parts.append(f"Current Medications: {', '.join(hp_meds)}")
                if parts:
                    profile_context = (
                        "\n\nPatient Health Profile Context:\n"
                        + "\n".join(f"- {p}" for p in parts)
                        + "\n\nTake this health profile into account when evaluating symptoms.\n"
                    )
        finally:
            conn.close()

    prompt = f"""\
You are a medical AI assistant. A user has described their symptoms.

Symptoms: {req.symptoms}
Duration: {req.duration}
Severity (1-10): {req.severity}
{memory_context}{profile_context}
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
                # Send each chunk as an SSE text event
                safe = chunk.replace("\n", "\\n")
                yield f"data: {safe}\n\n"

            # Stream complete — parse JSON, save to DB & Mem0
            clean = buffer.strip()
            clean = _re.sub(r"```json\s*", "", clean)
            clean = _re.sub(r"```\s*", "", clean).strip()
            try:
                result = json.loads(clean)
            except Exception:
                result = {"error": "Could not parse AI response", "raw": buffer[:500]}

            # Save to DB
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

            # Save to Mem0
            if req.user_id and "condition" in result:
                summary = (
                    f"Patient reported: {req.symptoms}. "
                    f"Duration: {req.duration}, severity {req.severity}/10. "
                    f"AI suggested: {result.get('condition','unknown')} "
                    f"({result.get('severity','unknown')} severity, "
                    f"{result.get('confidence',0)}% confidence)."
                )
                try:
                    add_memory(
                        user_id=req.user_id,
                        content=summary,
                        metadata={"type": "symptom_check", "condition": result.get("condition", "")},
                    )
                except Exception as mem_err:
                    print(f"[stream] Mem0 save error: {mem_err}")

            # Final event with complete JSON for the frontend to render
            yield f"data: [DONE] {json.dumps(result)}\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering if deployed
        },
    )


# ── PDF download endpoint (Task 6) ──
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