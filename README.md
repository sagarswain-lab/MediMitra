---
title: MediMitra
emoji: 🌍
colorFrom: green
colorTo: blue
sdk: docker
app_file: app.py
pinned: false
license: mit
short_description: AI-Powered Health Intelligence Platform
---
# 🏥 MediMitra — AI-Powered Health Intelligence Platform

<div align="center">

![MediMitra Banner](https://img.shields.io/badge/MediMitra-AI%20Health%20Platform-1A7A4A?style=for-the-badge&logo=heart&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq AI](https://img.shields.io/badge/Groq-Llama%203.3-orange?style=flat-square&logo=linux&logoColor=white)](https://console.groq.com)
[![HTML5](https://img.shields.io/badge/HTML5-CSS3-E34F26?style=flat-square&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

### *Your AI Health Companion — Smarter Healthcare Decisions for Every Indian*

**Built for FutureAI Global Hackathon 2026**

## 🚀 Deployment Links

| Service | URL |
|---------|-----|
| 🌐 **Live Demo** | [https://sagarswain-lab.github.io/MediMitra/medimitra-frontend/medimitra_spa.html](https://sagarswain-lab.github.io/MediMitra/medimitra-frontend/medimitra_spa.html) |
| 🔗 **Backend API** | [https://medimitra-api-05bj.onrender.com/](https://medimitra-api-05bj.onrender.com/) |
| 📖 **API Documentation** | [https://medimitra-api-05bj.onrender.com/docs](https://medimitra-api-05bj.onrender.com/docs) |

<br/>

![MediMitra Full Demo](medimitra_overall_demo_1773854250611.webp)

</div>

---

## 📌 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Installation & Setup](#-installation--setup)
- [⚠️ Port Conflict Fix](#️-port-conflict-fix-important-for-judges)
- [How to Run](#-how-to-run)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Technical Workflow](#-technical-workflow)
- [Team](#-team)

---

## 🎯 Problem Statement

India faces three critical overlapping health crises:

- **25%+ of drugs** sold in rural India are counterfeit or substandard
- Millions of patients receive prescriptions they **cannot read or understand** due to language barriers
- **Self-medication errors** cause thousands of hospitalizations yearly
- Rural populations have **zero access** to basic health literacy tools in their native language

Most existing health apps target urban, English-speaking users — leaving 700 million rural Indians underserved.

---

## 💡 Solution Overview

**MediMitra** is a comprehensive AI-powered health companion web application that bridges the healthcare literacy gap for Indian users. It combines 7 intelligent features into one seamless platform.

> *"MediMitra" means "Health Friend" in Hindi/Odia — because everyone deserves a knowledgeable health companion.*

---

## ✨ Key Features

### 🤒 1. Symptom Checker
- User describes symptoms via text or **voice input**
- AI analyzes and identifies possible conditions with confidence score
- Provides plain-language explanation, home remedies, and red flag warnings
- **⚡ SSE Streaming** — tokens stream word-by-word in real time; users see results in < 300 ms
- **Language-dependent** — responds in user's selected language
- Results saved with **Mem0** persistent memory for personalized future visits

### 📄 2. Prescription Reader
- Upload photo of handwritten or printed prescription
- OCR extracts medicine names and dosages
- AI explains each medicine in simple language
- **Text-to-Speech** reads explanation aloud
- Supports **7 Indian languages**

### ⚠️ 3. Drug Interaction Checker
- Enter multiple medicines via search or voice
- Checks dangerous combinations using **OpenFDA clinical data**
- Color-coded interaction matrix (Safe / Moderate / Dangerous)
- Printable doctor summary report

### 📸 4. Medicine Scanner
- Upload or capture medicine packaging photo
- AI verifies authenticity using **OpenFDA database**
- Safety score (0-100) with animated circular display
- Verdict: Genuine / Suspicious / Counterfeit

### 🥗 5. Lifestyle Advisor
- Personalized health profile input (age, BMI, conditions, goals)
- AI generates complete **7-day diet + exercise + wellness plan**
- Tailored for Indian food preferences and health conditions
- **Language-dependent** — plan generated in selected language

### 🌦️ 6. Seasonal Health Awareness
- Auto-detects user location via GPS
- Shows season-specific health alerts (Monsoon/Winter/Summer)
- Real disease risk cards with prevention tips
- Do's & Don'ts + seasonal diet recommendations

### 📍 7. Nearby Healthcare Finder
- Real-time GPS location detection
- Finds actual hospitals, clinics, pharmacies using **Overpass API** (OpenStreetMap)
- Interactive map powered by **Leaflet.js** (100% free, no API key)
- Filter by type and radius (1km / 2km / 5km / 10km)

---

## 📊 Analytics & Feedback
### 💬 Integrated Feedback System
- Interactive star-rating and comment system built into the dashboard.
- Persistent storage of user ratings in **SQLite3** for continuous platform improvement.
- Full-stack feedback loop with a dedicated backend route and database table.

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| HTML5 + CSS3 + Vanilla JS | Single Page Application (SPA) — zero framework |
| `app.js` + `style.css` | All SPA logic and design system |
| Leaflet.js + OpenStreetMap | Free interactive maps (no API key) |
| Web Speech API | Voice input & text-to-speech output |
| Font Awesome | Icons |
| Sora + DM Sans (Google Fonts) | Typography |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI (Python) | REST API framework |
| Groq Llama 3.3 70B | Text AI — symptoms, lifestyle, drug interaction |
| Groq Llama 4 Scout (Vision) | Multimodal AI — prescription reader, medicine scanner |
| ReportLab | PDF generation (symptom reports, 7-day plans) |
| SQLite3 | Lightweight local database |
| Pydantic v2 | Request/response validation with coercion validators |
| Mem0 | Persistent AI memory for returning users |
| Uvicorn | ASGI server |

### External APIs (All Free)
| API | Purpose | Key Required |
|---|---|---|
| Groq API | All AI responses (text + vision) | ✅ Free key |
| OpenFDA API | Drug verification & interaction data | ❌ No key |
| Overpass API | Real nearby places (hospitals, clinics) | ❌ No key |
| Mem0 API | Persistent user memory (optional) | ✅ Free key (optional) |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
│                                                         │
│  MediMitra SPA (HTML/CSS/JS)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Symptom  │  │Prescription│ │ Nearby   │  ...         │
│  │ Checker  │  │  Reader   │ │Healthcare│               │
│  └────┬─────┘  └────┬──────┘ └────┬─────┘               │
│       │              │              │                   │
│       └──────────────┴──────────────┘                   │
│                      │                                  │
│  fetch() POST + ReadableStream SSE to Render Backend    │
└──────────────────────┼──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 FastAPI BACKEND                         │
│              (Deployed on Render)                       │
│                                                         │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │symptom  │ │prescriptn│ │lifestyle │ │ nearby   │     │
│  │.py      │ │.py       │ │.py       │ │.py       │     │
│  └────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘     │
│       │             │             │           │         │
│  ┌────▼─────────────▼─────────────▼─┐  ┌──────▼─────┐   │
│  │      llm_service.py              │  │overpass_   │   │
│  │   (Groq Llama 3.3 / Llama 4)       │service.py  │   │
│  └──────────────────────────────────┘  └────────────┘   │
│                                                         │
│  ┌──────────────────┐  ┌───────────────────────────┐    │
│  │  openfda_service │  │    SQLite3 Database       │    │
│  │  .py             │  │    (medimitra.db)         │    │
│  └──────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Any modern web browser (Chrome recommended)
- Internet connection (for AI API calls)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/sagarswain-lab/MediMitra.git
cd MediMitra
```

### Step 2 — Install Backend Dependencies
```bash
cd medimitra-backend
pip install -r requirements.txt
```

### Step 3 — Environment Variables
Get a free Groq API key from:
👉 **https://console.groq.com**

Then update `.env`:
```env
GROQ_API_KEY=your_key_here
```

---

## ⚠️ Port Conflict Fix (Important for Judges)

If you previously ran another project using port `8001` or `5500`, those servers
may still be running in the background — even after closing the terminal window.
This will cause MediMitra to fail silently or show the wrong project's output.

**Before running MediMitra, always clear both ports first:**

### Windows
```cmd
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8001') do taskkill /PID %a /F
for /f "tokens=5" %a in ('netstat -ano ^| findstr :5500') do taskkill /PID %a /F
```

### macOS / Linux
```bash
lsof -ti :8001 | xargs kill -9
lsof -ti :5500 | xargs kill -9
```

**Then verify both ports are free:**

### Windows
```cmd
netstat -ano | findstr :8001
netstat -ano | findstr :5500
```

### macOS / Linux
```bash
lsof -i :8001
lsof -i :5500
```

If **nothing shows up** for both — ports are free ✅ You can now safely run MediMitra.

> 💡 **Tip:** Always press `Ctrl+C` in the terminal before closing it to gracefully
> stop the server and free the port automatically.

---

## 🚀 How to Run

### Terminal 1 — Start Backend

> 💡 **Important:** Ensure you have installed the dependencies by running `pip install -r requirements.txt` inside the `medimitra-backend` folder before starting.

```
cd medimitra-backend
pip install -r requirements.txt
python run_backend.py
```

You should see:
```
 Starting MediMitra Backend on port 8001...
 MediMitra API running on http://localhost:8001
INFO: Application startup complete.
```

### Terminal 2 — Start Frontend

Open a **new terminal window**:

```
cd medimitra-frontend
python run_frontend.py
```

You should see:
```
 MediMitra Frontend running at http://localhost:5500/medimitra_spa.html
 Opening browser automatically...
```

**The browser will open automatically!** 🎉

### Access Points
| Service | URL |
|---|---|
| 🌐 Web App (Local) | http://localhost:5500/medimitra_spa.html |
| 📖 API Docs (Local) | http://localhost:8001/docs |
| ❤️ Health Check (Local) | http://localhost:8001/health |

---

## 📡 API Endpoints

All endpoints are available at `http://localhost:8001` (local) or `https://medimitra-api-05bj.onrender.com/` (deployed)

| Method | Endpoint | Feature | Description |
|---|---|---|---|
| POST | `/api/symptom/check` | Symptom Checker | Analyze symptoms, return full JSON diagnosis |
| POST | `/api/symptom/stream` | Symptom Checker (SSE) | ⚡ Stream AI tokens live via Server-Sent Events |
| POST | `/api/symptom/download-pdf` | Symptom Report | Download branded PDF of symptom analysis |
| POST | `/api/prescription/read` | Prescription Reader | Extract and explain prescription medicines |
| POST | `/api/interaction/check` | Drug Interaction | Check interactions between medicines |
| POST | `/api/scanner/verify` | Medicine Scanner | Verify medicine authenticity |
| POST | `/api/lifestyle/plan` | Lifestyle Advisor | Generate 7-day wellness plan |
| POST | `/api/lifestyle/download-pdf` | Lifestyle Report | Download branded PDF of 7-day plan |
| POST | `/api/seasonal/alerts` | Seasonal Awareness | Get seasonal health alerts by location |
| POST | `/api/nearby/find` | Nearby Healthcare | Find hospitals/clinics/pharmacies nearby |
| POST | `/api/feedback/submit` | User Feedback | Submit user rating and comments |
| POST | `/api/auth/google` | Authentication | Verify Google OAuth token, return JWT |
| GET | `/api/auth/config` | Auth Config | Return Google Client ID for frontend |
| GET | `/api/profile/me` | User Profile | Get authenticated user's health profile |
| PUT | `/api/profile/me` | User Profile | Update authenticated user's health profile |
| GET | `/docs` | API Docs | Interactive Swagger documentation |
| GET | `/health` | Health Check | Server status check |

### Sample Request — Symptom Checker
```json
POST /api/symptom/check
{
  "symptoms": "fever since 2 days, headache, body pain",
  "duration": "1-3 days",
  "severity": "6",
  "language": "Hindi"
}
```

### Sample Response
```json
{
  "condition": "Viral Fever",
  "severity": "Moderate",
  "confidence": 82,
  "explanation": "यह एक सामान्य वायरल बुखार प्रतीत होता है...",
  "home_remedies": ["आराम करें और पानी पियें", "..."],
  "red_flags": ["3 दिनों से अधिक बुखार", "..."]
}
```

---

## 📁 Project Structure

```
MediMitra/
│
├── 📁 medimitra-backend/          # FastAPI Python Backend
│   ├── 📄 main.py                 # App entry point, CORS, routes
│   ├── 📄 database.py             # SQLite3 setup & initialization
│   ├── 📄 requirements.txt        # Python dependencies
│   ├── 📄 run_backend.py          # Easy start script
│   ├── 📄 auth_utils.py           # JWT auth helpers
│   ├── 📄 .env                    # API keys (Groq, Mem0, Google)
│   ├── 📄 .gitignore              # Git ignore rules
│   │
│   ├── 📁 routes/                 # Feature route handlers
│   │   ├── 📄 symptom.py          # Symptom checker + SSE stream + PDF download
│   │   ├── 📄 prescription.py     # Prescription reader (vision AI)
│   │   ├── 📄 interaction.py      # Drug interaction endpoint
│   │   ├── 📄 scanner.py          # Medicine scanner (vision AI)
│   │   ├── 📄 lifestyle.py        # Lifestyle advisor + PDF download
│   │   ├── 📄 seasonal.py         # Seasonal awareness endpoint
│   │   ├── 📄 nearby.py           # Nearby healthcare endpoint
│   │   ├── 📄 auth.py             # Google OAuth + JWT endpoints
│   │   ├── 📄 profile.py          # User health profile endpoints
│   │   └── 📄 feedback.py         # User feedback endpoint
│   │
│   ├── 📁 services/               # Business logic & external integrations
│   │   ├── 📄 llm_service.py      # Groq SDK wrapper (text + vision + streaming)
│   │   ├── 📄 pdf_service.py      # ReportLab PDF generator (Indic Unicode support)
│   │   ├── 📄 memory_service.py   # Mem0 persistent AI memory
│   │   ├── 📄 openfda_service.py  # OpenFDA drug database
│   │   └── 📄 overpass_service.py # Overpass/OpenStreetMap API
│   │
│   └── 📁 models/
│       └── 📄 schemas.py          # Pydantic v2 models with coercion validators
│
├── 📁 medimitra-frontend/         # Frontend Web App
│   ├── 📄 medimitra_spa.html      # Complete Single Page Application
│   ├── 📄 app.js                  # All SPA logic, state, API calls, i18n
│   ├── 📄 style.css               # Full design system & animations
│   └── 📄 run_frontend.py         # Easy start script (auto-opens browser)
│
└── 📄 README.md                   # This file
```

---

## 🔄 Technical Workflow

### How Symptom Checker Works (SSE Streaming)
```
User types/speaks symptoms
        ↓
Web Speech API captures voice (optional)
        ↓
Frontend sends POST to /api/symptom/stream
        ↓
FastAPI validates request (Pydantic)
Mem0 fetches relevant past visit memories
Health profile context injected into prompt
        ↓
Groq Llama 3.3 (stream=True) starts generating
        ↓
┌─────────────────────────────────────┐
│  Tokens stream via SSE in real time │
│  Frontend ReadableStream reader     │
│  renders words live in result card  │
│  < 300 ms to first visible token   │
└─────────────────────────────────────┘
        ↓
[DONE] event fires → full JSON parsed
        ↓
Result saved to SQLite3 database
Summary saved to Mem0 memory store
        ↓
Frontend renders styled result card
(condition, confidence bar, tabs)
        ↓
Result saved to session history
```

> **Fallback**: if streaming fails, the frontend automatically retries with the non-streaming `/api/symptom/check` endpoint so the app never breaks.

### How Nearby Healthcare Works
```
User clicks "Detect My Location"
        ↓
HTML5 Geolocation API gets GPS coords
        ↓
Frontend sends POST to /api/nearby/find
        ↓
Backend queries Overpass API
(OpenStreetMap) for real places
        ↓
Returns hospitals, clinics, pharmacies
with real names, addresses, coordinates
        ↓
Frontend renders on Leaflet.js map
with color-coded markers
        ↓
All data cached locally —
radius/type filter works instantly
without any new API call
```

---

## 🌟 Innovation Highlights

| Feature | Innovation |
|---|---|
| **⚡ SSE Streaming** | Groq tokens stream live — first word visible in < 300 ms, no waiting |
| **🧠 Persistent Memory** | Mem0 remembers past visits — AI personalises every new analysis |
| **🔐 Google Auth** | One-click Google Sign-In, JWT sessions, health profile per user |
| **📄 Multilingual PDFs** | ReportLab PDFs render Hindi/Bengali/Tamil/Telugu/Odia/Marathi natively via Unicode font (cross-platform: Windows + Linux/Render) |
| **🌐 Full UI Translation** | Switching language instantly translates all nav, labels, buttons and card text — not just AI output |
| **🔑 Groq Key Rotation** | Multiple GROQ API keys supported — auto-rotates on rate limit hit |
| **Free Maps** | Leaflet + OpenStreetMap — zero cost, real data |
| **Free Drug Data** | OpenFDA API — no key, real clinical data |
| **Real Nearby Places** | Overpass API — actual OSM database, not fake data |
| **Voice Input** | Web Speech API — works for symptoms + medicines |
| **Offline History** | localStorage — history works without backend |
| **SPA Architecture** | Single HTML + JS + CSS — zero framework, instant load |
| **Smart Caching** | Nearby data cached once — filter/radius changes are instant |

---

## 📊 Judging Criteria Alignment

| Criteria | How MediMitra Addresses It |
|---|---|
| **Functionality** | 7 fully working AI features with real API integrations |
| **Code Quality** | Modular structure, Pydantic validation, separation of concerns |
| **Scalability** | FastAPI + SQLite easily upgrades to PostgreSQL; stateless routes |
| **Innovation** | Multilingual AI + free APIs + voice input + real map data |
| **Social Impact** | Targets rural India's health literacy gap in their own language |

---

## 🧪 Automated Testing with Keploy

MediMitra includes automated API regression tests using **Keploy**. Keploy records and plays back HTTP request-response payloads to verify that backend modifications do not break existing endpoints.

### How to Run Tests

1. Make sure you have the Keploy CLI installed.
2. Run the test suite:
   ```bash
   make test-api
   ```
   Or directly run Keploy:
   ```bash
   cd medimitra-backend
   keploy test -c "python run_backend.py"
   ```

### How to Record New Test Cases

If you introduce new endpoints or modify request schemas, you can record new test cases by following these steps:

1. Start the backend in record mode:
   ```bash
   cd medimitra-backend
   keploy record -c "python run_backend.py"
   ```
2. Interact with the application or send HTTP requests to the target endpoints (e.g., using Postman, curl, or the Swagger UI at `http://localhost:8001/docs`).
3. Stop the backend server. Keploy will capture the API traffic and automatically generate new test cases under the `medimitra-backend/keploy/tests/` directory as YAML files.

---

## 🩺 Medical Disclaimer

> MediMitra provides AI-generated health information for educational purposes only. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed healthcare professional for medical concerns.

---

## 👨‍💻 Team

**Team Name:** SuperNova
| Name | Role |
|---|---|
| **Sagar Swain** | Backend Developer |
| **Aavash Kumar Beriha** | Frontend Developer |
| **Om Rudra Prakash** | Supportive Backend Developer |
| **Anup Kumar Sahoo** | Presentation & Documentation |

**Institution:** ITER — SOA<br>

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ by team SuperNova 2026**

*MediMitra — Because every Indian deserves a health companion in their own language*

</div>
