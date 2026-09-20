from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    name: Optional[str] = None
    username: str = Field(..., min_length = 3, max_length = 20)
    email: EmailStr = Field(..., max_length = 255)
    bio: Optional[str] = None

    city: Optional[str] = None
    university: Optional[str] = None
    institute: Optional[str] = None
    group: Optional[str] = None

    password: str = Field(..., min_length = 4, max_length = 10)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: str = Field(..., min_length = 3, max_length = 20)
    email: EmailStr = Field(..., max_length = 255)
    bio: Optional[str] = None

    city: Optional[str] = None
    university: Optional[str] = None
    institute: Optional[str] = None
    group: Optional[str] = None

class PasswordUpdate(BaseModel):
    old_password: str = Field(min_length = 3, max_length = 10)
    new_password: str = Field(min_length = 3, max_length = 10)