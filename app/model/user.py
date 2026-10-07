import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base

class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name: Mapped[str | None] = mapped_column(String(20))
    username: Mapped[str] = mapped_column(String(20), unique = True, index = True)
    email: Mapped[str] = mapped_column(String(255), unique = True, index = True)
    bio: Mapped[str | None] = mapped_column(String(60))
    avatar_key: Mapped[str | None] = mapped_column(String(500))

    city: Mapped[str| None] = mapped_column(String(20), index = True)
    university: Mapped[str | None] = mapped_column(String(20), index = True)
    institute: Mapped[str | None] = mapped_column(String(15), index = True)
    group: Mapped[str | None] = mapped_column(String(20), index = True)

    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())
