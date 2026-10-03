import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from app.core import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String(20), nullable = True)
    username = Column(String(20), unique = True, index = True, nullable = False)
    email = Column(String(255), unique = True, index = True,  nullable = False)
    bio = Column(String(60), nullable = True)

    city = Column(String(20), index = True, nullable = True)
    university = Column(String(20), index = True, nullable = True)
    institute = Column(String(15), index = True, nullable = True)
    group = Column(String(20), index = True, nullable = True)

    hashed_password = Column(String(255), nullable = False)
    is_active = Column(Boolean, default = False, nullable = False)
    created_at = Column(DateTime(timezone = True), server_default = func.now(), nullable = False)
