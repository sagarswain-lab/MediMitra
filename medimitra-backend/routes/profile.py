from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from models.schemas import HealthProfileRequest, HealthProfileResponse
from auth_utils import get_current_user
from database import get_connection
from services.memory_service import store_profile_memory
import json
import io

router = APIRouter()

_SELECT = (
    "SELECT id, user_id, full_name, age, gender, blood_group, height_cm, weight_kg, "
    "allergies, chronic_conditions, current_medications, past_surgeries, "
    "emergency_contact_name, emergency_contact_phone, emergency_contact_relation, "
    "emergency_contact, updated_at "
    "FROM health_profiles WHERE user_id = ?"
)


def _row_to_response(row) -> HealthProfileResponse:
    return HealthProfileResponse(
        id=row["id"],
        user_id=row["user_id"],
        full_name=row["full_name"],
        age=row["age"],
        gender=row["gender"],
        blood_group=row["blood_group"],
        height_cm=row["height_cm"],
        weight_kg=row["weight_kg"],
        allergies=json.loads(row["allergies"]) if row["allergies"] else [],
        chronic_conditions=json.loads(row["chronic_conditions"]) if row["chronic_conditions"] else [],
        current_medications=json.loads(row["current_medications"]) if row["current_medications"] else [],
        past_surgeries=json.loads(row["past_surgeries"]) if row["past_surgeries"] else [],
        emergency_contact_name=row["emergency_contact_name"],
        emergency_contact_phone=row["emergency_contact_phone"],
        emergency_contact_relation=row["emergency_contact_relation"],
        emergency_contact=row["emergency_contact"],
        updated_at=str(row["updated_at"]) if row["updated_at"] else None,
    )


@router.get("/me", response_model=HealthProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        row = conn.execute(_SELECT, (user_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Health profile not found. Please create one.")

    return _row_to_response(row)


@router.put("/me", response_model=HealthProfileResponse)
async def upsert_my_profile(req: HealthProfileRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM health_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()

        allergies_str   = json.dumps(req.allergies or [])
        chronic_str     = json.dumps(req.chronic_conditions or [])
        meds_str        = json.dumps(req.current_medications or [])
        surgeries_str   = json.dumps(req.past_surgeries or [])

        # Build a legacy emergency_contact string for backwards compat
        legacy_ec = req.emergency_contact
        if not legacy_ec and req.emergency_contact_name:
            parts = [req.emergency_contact_name]
            if req.emergency_contact_relation:
                parts.append(f"({req.emergency_contact_relation})")
            if req.emergency_contact_phone:
                parts.append(req.emergency_contact_phone)
            legacy_ec = " ".join(parts)

        if existing:
            conn.execute("""
                UPDATE health_profiles
                SET full_name = ?, age = ?, gender = ?, blood_group = ?,
                    height_cm = ?, weight_kg = ?,
                    allergies = ?, chronic_conditions = ?, current_medications = ?,
                    past_surgeries = ?,
                    emergency_contact_name = ?, emergency_contact_phone = ?,
                    emergency_contact_relation = ?,
                    emergency_contact = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                req.full_name, req.age, req.gender, req.blood_group,
                req.height_cm, req.weight_kg,
                allergies_str, chronic_str, meds_str, surgeries_str,
                req.emergency_contact_name, req.emergency_contact_phone,
                req.emergency_contact_relation,
                legacy_ec,
                user_id
            ))
        else:
            conn.execute("""
                INSERT INTO health_profiles
                    (user_id, full_name, age, gender, blood_group, height_cm, weight_kg,
                     allergies, chronic_conditions, current_medications, past_surgeries,
                     emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
                     emergency_contact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                req.full_name, req.age, req.gender, req.blood_group,
                req.height_cm, req.weight_kg,
                allergies_str, chronic_str, meds_str, surgeries_str,
                req.emergency_contact_name, req.emergency_contact_phone,
                req.emergency_contact_relation,
                legacy_ec
            ))

        conn.commit()
        row = conn.execute(_SELECT, (user_id,)).fetchone()
    finally:
        conn.close()

    resp = _row_to_response(row)
    # Persist profile to Mem0 so all AI routes benefit from personalisation
    store_profile_memory(str(user_id), resp.dict())
    return resp


@router.get("/health-card-pdf")
async def download_health_card_pdf(current_user: dict = Depends(get_current_user)):
    """
    Generate and stream the user's health profile as a branded PDF with user's profile picture.
    GET /api/profile/health-card-pdf
    """
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        row = conn.execute(_SELECT, (user_id,)).fetchone()
        # Also fetch user's picture from users table
        user_row = conn.execute("SELECT picture FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Health profile not found. Please save your profile first.")

    profile = _row_to_response(row).dict()
    picture_url = user_row["picture"] if user_row and user_row["picture"] else None

    try:
        from services.pdf_service import generate_health_card_pdf
        pdf_bytes = generate_health_card_pdf(profile, picture_url=picture_url)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="medimitra_health_card.pdf"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
