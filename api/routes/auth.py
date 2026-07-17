"""
Auth Routes
"""

from fastapi import APIRouter, HTTPException

from api.auth import create_access_token

router = APIRouter()


@router.post("/login")
async def login(email: str, password: str):
    """Login endpoint - returns JWT token."""
    # TODO: Implement user lookup from database
    # For now, hardcoded admin
    if email == "admin@empresa.com" and password == "admin123":
        token = create_access_token({"sub": email, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register")
async def register():
    """Register new user (admin only)."""
    # TODO: Implement user registration
    pass


@router.get("/me")
async def get_me():
    """Get current user info."""
    # TODO: Implement with JWT dependency
    return {"email": "admin@empresa.com", "role": "admin"}
