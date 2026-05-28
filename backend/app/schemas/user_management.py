from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    department_id: UUID | None = None
    organization_id: UUID
    role_id: UUID | None = None
    send_welcome_email: bool = True


class UserCreateResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    department_id: UUID | None
    organization_id: UUID | None
    role: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    department_id: UUID | None = None
    role_id: UUID | None = None
    is_active: bool | None = None


class UserDetailResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    department_id: UUID | None
    organization_id: UUID | None
    role: str | None
    is_active: bool
    is_verified: bool
    is_first_login: bool
    must_change_password: bool
    failed_login_attempts: int
    locked_until: datetime | None
    last_login: datetime | None
    password_changed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserDetailResponse]
    total_count: int
    page: int
    page_size: int


class UserFilterRequest(BaseModel):
    organization_id: UUID | None = None
    department_id: UUID | None = None
    role: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    search_query: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BulkUserError(BaseModel):
    row_number: int
    email: str
    error_reason: str


class BulkUserUploadResponse(BaseModel):
    total_rows: int
    successfully_created: int
    failed_rows: int
    errors: list[BulkUserError]
    created_users: list[UserCreateResponse]


class PasswordResetByAdminRequest(BaseModel):
    user_id: UUID
    force_change_on_login: bool = True


class PasswordResetByAdminResponse(BaseModel):
    user_id: UUID
    email: str
    temporary_password_sent: bool
    force_change_on_login: bool


class UserActivationRequest(BaseModel):
    user_id: UUID
    is_active: bool
    reason: str | None = None


class UserActivationResponse(BaseModel):
    user_id: UUID
    email: str
    is_active: bool
    updated_at: datetime


class SuperAdminDashboardStats(BaseModel):
    total_organizations: int
    total_users: int
    active_users: int
    inactive_users: int
    unverified_users: int
    locked_accounts: int
    users_created_today: int
    users_created_this_month: int
    departments_count: int
    recent_user_activity: list[dict]
