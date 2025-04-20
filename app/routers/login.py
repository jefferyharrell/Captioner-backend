import os

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

@router.post("/login")
async def login(body: LoginRequest) -> JSONResponse:
    env_password = os.getenv("BACKEND_PASSWORD")
    if body.password == env_password:
        return JSONResponse(
            {"detail": "Login successful"},
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        {"detail": "Invalid password"},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
