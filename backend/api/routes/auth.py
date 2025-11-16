"""Authentication API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """User registration endpoint (to be implemented)."""
    return {"message": "Registration endpoint - implementation pending"}


@router.post("/login")
async def login():
    """User login endpoint (to be implemented)."""
    return {"message": "Login endpoint - implementation pending"}


@router.post("/logout")
async def logout():
    """User logout endpoint (to be implemented)."""
    return {"message": "Logout endpoint - implementation pending"}
