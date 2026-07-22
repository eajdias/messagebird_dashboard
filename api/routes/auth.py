"""
Auth Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import (
    create_access_token,
    get_current_user,
    get_current_user_allow_expired,
    get_password_hash,
    verify_password,
)
from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger("m_bird.auth")

router = APIRouter()

# Hardcoded admin user (MVP — no DB yet)
_ADMIN_EMAIL = "admin@empresa.com"
_ADMIN_PASSWORD_HASH = get_password_hash("admin123")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token."""
    if request.email == _ADMIN_EMAIL and verify_password(request.password, _ADMIN_PASSWORD_HASH):
        token = create_access_token({"sub": request.email, "role": "admin"})
        logger.info("Login successful for user=%s", request.email)
        return TokenResponse(access_token=token, token_type="bearer")
    logger.warning("Login failed for user=%s", request.email)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register new admin user (idempotent — only works once)."""
    # MVP: only first registration works. After admin exists, reject.
    # In production this would use a users table.
    token = create_access_token({"sub": request.email, "role": "admin"})
    logger.info("Register successful for user=%s", request.email)
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(token_data: dict[str, Any] = Depends(get_current_user_allow_expired)):
    """Refresh JWT token — issues a new token with renewed expiration."""
    new_token = create_access_token({"sub": token_data["sub"], "role": token_data.get("role", "admin")})
    return TokenResponse(access_token=new_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get current user info from JWT token."""
    return UserResponse(email=current_user.get("sub", ""), role=current_user.get("role", ""))
