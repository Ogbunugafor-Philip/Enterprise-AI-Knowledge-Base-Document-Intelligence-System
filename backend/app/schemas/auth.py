from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    organization_id: UUID | None
    department_id: UUID | None
    role: str | None
    is_active: bool
    is_verified: bool
    is_first_login: bool

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    must_change_password: bool


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str


class TokenData(BaseModel):
    user_id: UUID
    organization_id: UUID | None
    role: str | None = None
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class SuperAdminSetupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str


class SuperAdminSetupResponse(BaseModel):
    message: str
    email: EmailStr
    created_at: datetime
