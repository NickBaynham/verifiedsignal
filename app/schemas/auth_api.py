"""Request/response bodies for Supabase-backed session auth routes."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class EmailPasswordBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class ResetPasswordBody(BaseModel):
    email: EmailStr


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


class SignupResponse(BaseModel):
    message: str = "Check your email to confirm your account"
