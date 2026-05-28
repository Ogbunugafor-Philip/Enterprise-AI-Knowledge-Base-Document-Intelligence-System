from uuid import UUID

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    organization_id: UUID | None


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    resource: str
    action: str

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    organization_id: UUID | None
    permissions: list[PermissionResponse] = []

    model_config = {"from_attributes": True}


class PermissionAssignRequest(BaseModel):
    permission_ids: list[UUID]


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    organization_id: UUID


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    organization_id: UUID
    is_active: bool

    model_config = {"from_attributes": True}
