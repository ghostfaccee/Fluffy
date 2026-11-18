from pydantic import BaseModel, Field

class StoryCreate(BaseModel):
    title: str = Field(..., min_length = 1, max_length = 20)
    media_key: str = Field(...)

class StoryUploadRequest(BaseModel):
    content_type: str = Field(..., pattern = '^(image/(jpeg|png)|video/(mp4|mpeg))$')
