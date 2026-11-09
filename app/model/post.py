import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

class Post(Base):
    __tablename__ = 'posts'

    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('users.user_id', ondelete = 'CASCADE'), index = True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(4096))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())

    author: Mapped['User'] = relationship(
        foreign_keys = [author_id]
    )
