from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db


from routes import symptom, prescription, interaction, scanner, lifestyle, seasonal, nearby, feedback


load_dotenv()

app = FastAPI(
    title="MediMitra API",
    description="AI-powered health tech backend for MediMitra",
    version="1.0.0"
)

# ── CORS (allows frontend to talk to backend) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routes ──
app.include_router(symptom.router,      prefix="/api/symptom",      tags=["Symptom Checker"])
app.include_router(prescription.router, prefix="/api/prescription",  tags=["Prescription Reader"])
app.include_router(interaction.router,  prefix="/api/interaction",   tags=["Drug Interaction"])
app.include_router(scanner.router,      prefix="/api/scanner",       tags=["Medicine Scanner"])
app.include_router(lifestyle.router,    prefix="/api/lifestyle",     tags=["Lifestyle Advisor"])
app.include_router(seasonal.router,     prefix="/api/seasonal",      tags=["Seasonal Awareness"])
app.include_router(nearby.router,       prefix="/api/nearby",        tags=["Nearby Healthcare"])
app.include_router(feedback.router,     prefix="/api/feedback",      tags=["User Feedback"])

# ── Initialize database on startup ──
@app.on_event("startup")
async def startup_event():
    init_db()
    print("MediMitra API running on http://localhost:8001")

@app.get("/")
def root():
    return {
        "app": "MediMitra API",
        "version": "1.0.0",
        "status": "running",
        "docs": "http://localhost:8001/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}