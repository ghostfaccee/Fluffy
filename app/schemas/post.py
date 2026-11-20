from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas import UserResponse

class PostCreate(BaseModel):
    title: str = Field(..., min_length = 1, max_length = 200)
    content: str = Field(..., min_length = 1, max_length = 4096)
    media_key: str | None = Field(None)

class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length = 1, max_length = 200)
    content: str | None = Field(None, min_length = 1, max_length = 4096)
    media_key: str | None = Field(None)

class PostResponse(BaseModel):
    post_id: UUID
    title: str
    content: str
    media_url: str | None
    created_at: datetime
    author: UserResponse

class PostMediaUploadUrl(BaseModel):
    content_type: str = Field(..., pattern = '^(image/(jpeg|png)|video/(mp4|mpeg))$')
