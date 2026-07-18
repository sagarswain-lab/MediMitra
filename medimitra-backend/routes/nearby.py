from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import NearbyRequest, NearbyResponse
from services.memory_service import get_user_health_context
from services.overpass_service import get_nearby_places
from auth_utils import get_optional_user
from database import get_connection

router = APIRouter()


@router.post("/find", response_model=NearbyResponse)
async def find_nearby(
    req: NearbyRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    try:
        places = get_nearby_places(
            lat=req.latitude,
            lon=req.longitude,
            place_type=req.type,
            radius_km=req.radius
        )

        # Attach emergency contact if user is logged in and has a profile
        emergency_contact = None
        if current_user:
            user_id = current_user.get("user_id")
            if user_id:
                try:
                    conn = get_connection()
                    row = conn.execute(
                        "SELECT emergency_contact_name, emergency_contact_phone, emergency_contact_relation "
                        "FROM health_profiles WHERE user_id = ?",
                        (user_id,)
                    ).fetchone()
                    conn.close()
                    if row and row["emergency_contact_phone"]:
                        emergency_contact = {
                            "name": row["emergency_contact_name"] or "",
                            "phone": row["emergency_contact_phone"] or "",
                            "relation": row["emergency_contact_relation"] or ""
                        }
                except Exception as ec_err:
                    print(f"[nearby] Emergency contact fetch error (non-fatal): {ec_err}")

        return NearbyResponse(places=places, emergency_contact=emergency_contact)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
