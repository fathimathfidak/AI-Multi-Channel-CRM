"""FastAPI application entrypoint for the CRM backend."""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from backend.auth import (
    admin_user,
    authenticate_user,
    create_access_token,
    public_user,
)
from backend.config import cors_origins
from backend.database import engine
from backend.leads import router as leads_router
from backend.sales_persons import router as sales_persons_router
from backend.settings import router as settings_router
from backend.whatsapp_import import router as whatsapp_import_router

from test_meta_lead import app as webhook_app


app: FastAPI = webhook_app
app.title = "Meta Lead CRM Backend"
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
def login(credentials: LoginRequest) -> dict[str, Any]:
    """Authenticate an active user and return a bearer access token."""
    user = authenticate_user(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": public_user(user),
    }


@app.get("/admin/me")
def admin_me(user: dict[str, Any] = Depends(admin_user)) -> dict[str, Any]:
    """Return the authenticated administrator's safe profile."""
    return {"user": public_user(user)}


app.include_router(sales_persons_router)
app.include_router(leads_router)
app.include_router(settings_router)
app.include_router(whatsapp_import_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report API availability and PostgreSQL connectivity."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return {"status": "ok", "database": "unavailable"}
    return {"status": "ok", "database": "connected"}
