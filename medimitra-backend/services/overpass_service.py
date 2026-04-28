import requests
import math

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_nearby_places(lat: float, lon: float, place_type: str, radius_km: int):
    """Fetch real nearby hospitals, clinics, pharmacies using Overpass API."""
    radius_m = radius_km * 1000

    # Map our types to OpenStreetMap amenity tags
    type_map = {
        "hospital": ["hospital"],
        "clinic": ["clinic", "doctors"],
        "pharmacy": ["pharmacy"],
        "all": ["hospital", "clinic", "doctors", "pharmacy"]
    }
    amenities = type_map.get(place_type, type_map["all"])

    # Build a more efficient Overpass query using regex for multiple amenities
    regex_amenities = "|".join(amenities)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"{regex_amenities}"](around:{radius_m},{lat},{lon});
      way["amenity"~"{regex_amenities}"](around:{radius_m},{lat},{lon});
      relation["amenity"~"{regex_amenities}"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    try:
        print(f"Fetching nearby healthcare from Overpass for lat={lat}, lon={lon}, radius={radius_km}km")
        headers = {
            "User-Agent": "MediMitra/1.0 (HealthCare Finder Service)",
            "Accept": "application/json"
        }
        res = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"Overpass API error: Status {res.status_code}")
            # Raise exception to trigger frontend fallback to demo data
            raise Exception(f"Overpass API returned status {res.status_code}")

        elements = res.json().get("elements", [])
        places = []

        for el in elements:
            tags = el.get("tags", {})
            # Use name or a descriptive placeholder if name is missing
            amenity_type = tags.get("amenity", "healthcare").replace("_", " ").title()
            name = tags.get("name") or tags.get("name:en") or f"Unnamed {amenity_type}"

            # Get coordinates (out center provides 'center' for ways/relations)
            if "lat" in el and "lon" in el:
                place_lat, place_lon = el["lat"], el["lon"]
            elif "center" in el:
                place_lat, place_lon = el["center"]["lat"], el["center"]["lon"]
            else:
                continue # Skip if no coordinate found

            # Calculate distance
            dist = calculate_distance(lat, lon, place_lat, place_lon)

            # Determine simplified type for UI
            amenity = tags.get("amenity", "")
            if amenity == "hospital":
                ptype = "hospital"
            elif amenity == "pharmacy":
                ptype = "pharmacy"
            else:
                ptype = "clinic"

            # Opening hours
            opening = tags.get("opening_hours", "")
            is_open = True  # default assumption, could implement parser later

            places.append({
                "name": name,
                "type": ptype,
                "address": build_address(tags),
                "distance": round(dist, 1),
                "rating": 4.0,  # OSM doesn't have ratings
                "open": is_open,
                "lat": place_lat,
                "lon": place_lon
            })

        print(f"Successfully found {len(places)} locations nearby")
        # Sort by distance
        places.sort(key=lambda x: x["distance"])
        return places[:40]

    except Exception as e:
        print(f"Error in get_nearby_places: {e}")
        raise e # Re-raise to let the router handle it (returns 500)

def build_address(tags: dict) -> str:
    """Build a readable address from OSM tags."""
    parts = []
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    if not parts and tags.get("addr:full"):
        return tags["addr:full"]
    return ", ".join(parts) if parts else "Address not available"

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km using Haversine formula."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))