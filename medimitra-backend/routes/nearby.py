from fastapi import APIRouter, HTTPException
from models.schemas import NearbyRequest, NearbyResponse
from services.overpass_service import get_nearby_places

router = APIRouter()

@router.post("/find", response_model=NearbyResponse)
async def find_nearby(req: NearbyRequest):
    try:
        places = get_nearby_places(
            lat=req.latitude,
            lon=req.longitude,
            place_type=req.type,
            radius_km=req.radius
        )
        return NearbyResponse(places=places)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))