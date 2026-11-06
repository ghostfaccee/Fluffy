from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field
from app.schemas import UserResponse

class MessageResponse(BaseModel):
    message_id: UUID
    sender_id: UUID
    content: str
    is_read: bool
    created_at: datetime
    sender: UserResponse

class MessageCreate(BaseModel):
    content: str = Field(..., min_length = 1, max_length = 4000)
