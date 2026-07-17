"""
auth_utils.py — JWT creation/verification + FastAPI dependency.

Uses python-jose with HS256.
JWT_SECRET must be set in .env — generate with:
    python -c "import secrets; print(secrets.token_hex(32))"
"""
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_to_a_secure_secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 days

_bearer = HTTPBearer(auto_error=False)


def create_jwt(payload: dict) -> str:
    """Create a signed JWT that expires in JWT_EXPIRE_HOURS hours."""
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict:
    """Verify and decode a JWT. Raises HTTPException 401 on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency — extracts the logged-in user from the Bearer token.

    Returns the decoded JWT payload dict (contains 'sub', 'email', 'name', 'picture', 'user_id').
    Raises 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return verify_jwt(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict | None:
    """
    FastAPI dependency — like get_current_user but returns None instead of 401
    when no token is present. Useful for routes that work for both
    authenticated and anonymous users.
    """
    if credentials is None:
        return None
    try:
        return verify_jwt(credentials.credentials)
    except HTTPException:
        return None
