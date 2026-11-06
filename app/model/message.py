import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

class Message(Base):
    __tablename__ = 'messages'

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('users.user_id'), index = True)
    receiver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('users.user_id'), index = True)
    content: Mapped[str] = mapped_column(String(4000))
    is_read: Mapped[bool] = mapped_column(Boolean, default = False, index = True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())

    sender: Mapped['User'] = relationship(
        foreign_keys = [sender_id],
        lazy = 'selectin'
    )

    receiver: Mapped['User'] = relationship(
        foreign_keys = [receiver_id],
        lazy = 'selectin'
    )

    __table_args__: tuple = (
        Index('ix_messages_dialog', 'sender_id', 'receiver_id', 'created_at'),
    )
