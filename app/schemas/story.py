from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas import UserResponse

class StoryCreate(BaseModel):
    title: str = Field(..., min_length = 1, max_length = 20)
    media_key: str = Field(...)

class StoryUploadRequest(BaseModel):
    content_type: str = Field(..., pattern = '^(image/(jpeg|png)|video/(mp4|mpeg))$')

class StoryUploadResponse(BaseModel):
    upload_url: str
    key: str

class StoryResponse(BaseModel):
    story_id: UUID
    title: str
    media_url: str
    created_at: datetime
    expires_at: datetime
    author: UserResponse
