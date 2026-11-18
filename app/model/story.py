import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import UUID, String, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

class Story(Base):
    __tablename__ = 'stories'

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True), 
        primary_key = True, 
        default = uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True), 
        ForeignKey('users.user_id', ondelete = 'CASCADE'), 
        index = True
    )
    title: Mapped[str] = mapped_column(String(20))
    media_key: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True), 
        default = func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc) + timedelta(hours = 24),
        index = True
    ) # index = True: The index will be useful for queries like WHERE expires_at > X, to retrieve active stories

    author: Mapped['User'] = relationship(
        foreign_keys = [author_id]
    )

    __table_args__ = (
        Index('ix_stories_author_expires', 'author_id', 'expires_at')
        # a composite index is required to retrieve an author's active stories
    )
