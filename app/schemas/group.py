from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse

class GroupCreate(BaseModel):
    name: str = Field(..., min_length = 1, max_length = 40)
    description: Optional[str] = Field(None, max_length = 200)

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length = 1, max_length = 40)
    description: Optional[str] = Field(None, max_length = 200)

class GroupResponse(BaseModel):
    group_id: UUID
    name: str
    description: Optional[str]
    avatar_url: Optional[str] = None
    invite_token: str
    created_at: datetime

class GroupMessageCreate(BaseModel):
    content: str = Field(..., min_length = 1, max_length = 4000)

class GroupMessageResponse(BaseModel):
    message_id: UUID
    group_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime
    sender: UserResponse

class GroupMemberResponse(BaseModel):
    user_id: UUID
    role: str
    joined_at: datetime

class GroupAvatarUploadUrlResponse(BaseModel):
    upload_url: str
    key: str

class GroupAvatarUploadRequest(BaseModel):
    content_type: str = Field(..., pattern = '^image/(jpeg|png)$')

class GroupAvatarSetRequest(BaseModel):
    key: str