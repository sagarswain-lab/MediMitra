"""
routes/auth.py — Google OAuth 2.0 Sign-In + JWT issuance.

POST /api/auth/google  — accepts Google ID token, returns JWT
GET  /api/auth/me      — returns current user profile from JWT
"""
import os
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.schemas import GoogleAuthRequest, AuthResponse, UserProfile
from auth_utils import create_jwt, get_current_user
from database import get_connection
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

@router.get("/config")
def get_auth_config():
    """Return public auth config (Google Client ID) to the frontend."""
    return {"google_client_id": GOOGLE_CLIENT_ID}


@router.post("/google", response_model=AuthResponse)
async def google_sign_in(req: GoogleAuthRequest):
    """
    Verify a Google ID token sent from the frontend.
    Creates the user on first login; returns a JWT on success.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In is not configured. Set GOOGLE_CLIENT_ID in .env",
        )

    # ── Verify the ID token with Google's public keys ──
    try:
        id_info = id_token.verify_oauth2_token(
            req.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")

    google_sub = id_info["sub"]
    email      = id_info.get("email", "")
    name       = id_info.get("name", "")
    picture    = id_info.get("picture", "")

    # ── Upsert into users table ──
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE google_sub = ?", (google_sub,)
        ).fetchone()

        if existing:
            user_id = existing["id"]
            conn.execute(
                "UPDATE users SET email=?, name=?, picture=? WHERE id=?",
                (email, name, picture, user_id),
            )
        else:
            cursor = conn.execute(
                "INSERT INTO users (google_sub, email, name, picture) VALUES (?,?,?,?)",
                (google_sub, email, name, picture),
            )
            user_id = cursor.lastrowid

        conn.commit()
    finally:
        conn.close()

    # ── Issue JWT ──
    token = create_jwt({
        "sub":     google_sub,
        "user_id": user_id,
        "email":   email,
        "name":    name,
        "picture": picture,
    })

    return AuthResponse(
        jwt=token,
        user_id=user_id,
        email=email,
        name=name,
        picture=picture,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    user_id = current_user.get("user_id")
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, google_sub, email, name, picture FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=row["id"],
        google_sub=row["google_sub"],
        email=row["email"],
        name=row["name"],
        picture=row["picture"],
    )
