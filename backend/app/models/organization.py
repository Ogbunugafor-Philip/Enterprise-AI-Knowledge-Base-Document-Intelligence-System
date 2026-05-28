import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    max_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    storage_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=10240)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    departments: Mapped[list["Department"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    permissions: Mapped[list["Permission"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="organization")
