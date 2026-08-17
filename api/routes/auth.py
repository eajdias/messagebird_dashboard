"""
Auth Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from api.auth import (
    create_access_token,
    get_current_user,
    get_current_user_allow_expired,
    get_password_hash,
    require_admin,
    verify_password,
)
from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger("m_bird.auth")

router = APIRouter()


async def _get_user_by_email(email: str) -> dict[str, Any] | None:
    from api.dependencies import get_pool

    pool = await get_pool()
    return await pool.fetch_one(
        "SELECT id, email, password_hash, role, name, active FROM users WHERE email = $1", email
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint — validates against database users table."""
    user = await _get_user_by_email(request.email)
    if user and user["active"] and verify_password(request.password, user["password_hash"]):
        token = create_access_token({"sub": user["email"], "role": user["role"], "user_id": user["id"]})
        logger.info("Login successful for user=%s", request.email)
        return TokenResponse(access_token=token, token_type="bearer")
    logger.warning("Login failed for user=%s", request.email)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    current_user: dict[str, Any] = Depends(require_admin),
):
    """Register a new user (admin only)."""
    from api.dependencies import get_pool

    pool = await get_pool()
    existing = await _get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    password_hash = get_password_hash(request.password)
    role = request.role if hasattr(request, "role") and request.role else "agent"
    await pool.execute(
        "INSERT INTO users (email, password_hash, role, name) VALUES ($1, $2, $3, $4)",
        request.email,
        password_hash,
        role,
        request.name or "",
    )
    logger.info("User registered: %s (role=%s)", request.email, role)
    return TokenResponse(access_token="", token_type="bearer")


@router.post("/change-password", response_model=UserResponse)
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Change own password (requires current password)."""
    from api.dependencies import get_pool

    user = await _get_user_by_email(current_user["sub"])
    if not user or not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")

    pool = await get_pool()
    new_hash = get_password_hash(new_password)
    await pool.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        new_hash,
        current_user["sub"],
    )
    logger.info("Password changed for user=%s", current_user["sub"])
    return UserResponse(email=current_user["sub"], role=current_user.get("role", ""))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(token_data: dict[str, Any] = Depends(get_current_user_allow_expired)):
    """Refresh JWT token — issues a new token with renewed expiration."""
    new_token = create_access_token(
        {
            "sub": token_data["sub"],
            "role": token_data.get("role", "agent"),
            "user_id": token_data.get("user_id"),
        }
    )
    return TokenResponse(access_token=new_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get current user info from JWT token."""
    return UserResponse(email=current_user.get("sub", ""), role=current_user.get("role", ""))
