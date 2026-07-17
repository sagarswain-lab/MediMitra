from fastapi import APIRouter, HTTPException, Depends
from models.schemas import HealthProfileRequest, HealthProfileResponse
from auth_utils import get_current_user
from database import get_connection
import json

router = APIRouter()

@router.get("/me", response_model=HealthProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, user_id, age, blood_group, allergies, chronic_conditions, current_medications, emergency_contact, updated_at FROM health_profiles WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Health profile not found. Please create one.")

    return HealthProfileResponse(
        id=row["id"],
        user_id=row["user_id"],
        age=row["age"],
        blood_group=row["blood_group"],
        allergies=json.loads(row["allergies"]) if row["allergies"] else [],
        chronic_conditions=json.loads(row["chronic_conditions"]) if row["chronic_conditions"] else [],
        current_medications=json.loads(row["current_medications"]) if row["current_medications"] else [],
        emergency_contact=row["emergency_contact"],
        updated_at=str(row["updated_at"])
    )

@router.put("/me", response_model=HealthProfileResponse)
async def upsert_my_profile(req: HealthProfileRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM health_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()

        allergies_str = json.dumps(req.allergies or [])
        chronic_str = json.dumps(req.chronic_conditions or [])
        meds_str = json.dumps(req.current_medications or [])

        if existing:
            conn.execute("""
                UPDATE health_profiles 
                SET age = ?, blood_group = ?, allergies = ?, chronic_conditions = ?, current_medications = ?, emergency_contact = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (req.age, req.blood_group, allergies_str, chronic_str, meds_str, req.emergency_contact, user_id))
        else:
            conn.execute("""
                INSERT INTO health_profiles (user_id, age, blood_group, allergies, chronic_conditions, current_medications, emergency_contact)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, req.age, req.blood_group, allergies_str, chronic_str, meds_str, req.emergency_contact))
        
        conn.commit()

        # Retrieve updated row
        row = conn.execute(
            "SELECT id, user_id, age, blood_group, allergies, chronic_conditions, current_medications, emergency_contact, updated_at FROM health_profiles WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    finally:
        conn.close()

    return HealthProfileResponse(
        id=row["id"],
        user_id=row["user_id"],
        age=row["age"],
        blood_group=row["blood_group"],
        allergies=json.loads(row["allergies"]) if row["allergies"] else [],
        chronic_conditions=json.loads(row["chronic_conditions"]) if row["chronic_conditions"] else [],
        current_medications=json.loads(row["current_medications"]) if row["current_medications"] else [],
        emergency_contact=row["emergency_contact"],
        updated_at=str(row["updated_at"])
    )
