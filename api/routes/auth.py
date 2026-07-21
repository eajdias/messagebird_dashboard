"""
Auth Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth import create_access_token, get_current_user
from api.schemas.auth import LoginRequest, TokenResponse, UserResponse

logger = logging.getLogger("m_bird.auth")

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token."""
    # TODO: Implement user lookup from database
    if request.email == "admin@empresa.com" and request.password == "admin123":
        token = create_access_token({"sub": request.email, "role": "admin"})
        logger.info("Login successful for user=%s", request.email)
        return TokenResponse(access_token=token, token_type="bearer")
    logger.warning("Login failed for user=%s", request.email)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register")
async def register():
    """Register new user (admin only)."""
    # TODO: Implement user registration
    pass


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get current user info from JWT token."""
    return UserResponse(email=current_user.get("sub", ""), role=current_user.get("role", ""))
