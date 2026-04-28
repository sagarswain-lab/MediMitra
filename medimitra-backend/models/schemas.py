from pydantic import BaseModel
from typing import List, Optional

# ── Symptom Checker ──
class SymptomRequest(BaseModel):
    symptoms: str
    duration: str
    severity: str
    language: Optional[str] = "English"

class SymptomResponse(BaseModel):
    condition: str
    severity: str
    confidence: int
    explanation: str
    home_remedies: List[str]
    red_flags: List[str]

# ── Prescription Reader ──
class PrescriptionRequest(BaseModel):
    image_base64: str
    language: str

class MedicineDetail(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str
    timing: str
    what_it_is: Optional[str] = ""
    what_it_treats: Optional[str] = ""
    side_effects: Optional[str] = ""

class PrescriptionResponse(BaseModel):
    medicines: List[MedicineDetail]
    explanation: str
    translated_text: str

# ── Drug Interaction ──
class InteractionRequest(BaseModel):
    medicines: List[str]
    language: Optional[str] = "English"

class InteractionDetail(BaseModel):
    drug_a: str
    drug_b: str
    risk: str
    explanation: str
    recommendation: str

class InteractionResponse(BaseModel):
    risk_level: str
    interactions: List[InteractionDetail]

# ── Medicine Scanner ──
class ScannerRequest(BaseModel):
    image_base64: str
    medicine_name: Optional[str] = ""
    language: Optional[str] = "English"

class ScannerDetails(BaseModel):
    drug_name: str
    manufacturer: str
    batch_number: str
    expiry: str
    openfda_status: str

class ScannerResponse(BaseModel):
    safety_score: int
    verdict: str
    details: ScannerDetails
    actions: List[str]

# ── Lifestyle Advisor ──
class LifestyleRequest(BaseModel):
    age: int
    height: float
    weight: float
    conditions: List[str]
    activity: str
    goal: str
    diet: str
    language: Optional[str] = "English"

class DayMeals(BaseModel):
    breakfast: str
    snack1: str
    lunch: str
    snack2: str
    dinner: str
    total_calories: int

class DayMorning(BaseModel):
    time: str
    drink: str
    activity: str

class DayExercise(BaseModel):
    type: str
    duration: str
    intensity: str
    routine: List[str]

class DayWellness(BaseModel):
    water: str
    sleep: str
    tip: str

class DayPlan(BaseModel):
    day: str
    morning: DayMorning
    meals: DayMeals
    exercise: DayExercise
    wellness: DayWellness

class LifestyleResponse(BaseModel):
    bmi: float
    plan: List[DayPlan]

# ── Seasonal Awareness ──
class SeasonalRequest(BaseModel):
    latitude: float
    longitude: float
    month: int
    language: Optional[str] = "English"

class DiseaseInfo(BaseModel):
    name: str
    risk: str
    symptoms: List[str]
    prevention: str

class SeasonalResponse(BaseModel):
    season: str
    alert: str
    season_css: str
    diseases: List[DiseaseInfo]
    dos: List[str]
    donts: List[str]
    diet_tips: List[str]

# ── Nearby Healthcare ──
class NearbyRequest(BaseModel):
    latitude: float
    longitude: float
    type: Optional[str] = "all"
    radius: Optional[int] = 2

class PlaceResult(BaseModel):
    name: str
    type: str
    address: str
    distance: float
    rating: float
    open: bool
    lat: float
    lon: float

class NearbyResponse(BaseModel):
    places: List[PlaceResult]

# ── User Feedback ──
class FeedbackRequest(BaseModel):
    rating: int
    feedback_text: Optional[str] = ""