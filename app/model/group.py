import uuid

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

class Group(Base):
    __tablename__ = 'groups'

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name: Mapped[str] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(String(200))
    avatar_key: Mapped[str | None] = mapped_column(String(500))

    invite_token: Mapped[str] = mapped_column(String(64), unique = True, index = True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())

class GroupMember(Base):
    __tablename__ = 'group_members'

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('groups.group_id', ondelete = 'CASCADE'), primary_key = True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('users.user_id', ondelete = 'CASCADE'), primary_key = True)

    role: Mapped[str] = mapped_column(String(10), default = 'member') # member, admin, owner

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())

    __table_args__ = (
        Index('ix_group_members_user', 'user_id'),
    )
    # Even though `user_id` is a primary key and is automatically indexed,
    #  we cannot efficiently execute SQL queries of the form 
    # `WHERE user_id = X`. This is because the index was created
    #  for `group_id` and `user_id` in that specific order.
    #  Queries such as `WHERE group_id = X AND user_id = X`
    #  and `WHERE group_id = X` will work perfectly well without additional indexes.

class GroupMessage(Base):
    __tablename__ = 'group_messages'

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('groups.group_id', ondelete = 'CASCADE')) # The index isn't needed; it will be covered by the composite index.
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('users.user_id', ondelete = 'CASCADE'), index = True)

    content: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), server_default = func.now())

    sender: Mapped['User'] = relationship(
        foreign_keys = [sender_id],
        lazy = 'selectin'
    ) # We implemented `selectin` to address the N+1 problem.

    __table_args__ = (
        Index('ix_group_messages_group_created', 'group_id', 'created_at'),
    )
    # This composite index is required to display the message history.