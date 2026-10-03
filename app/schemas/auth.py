from pydantic import BaseModel
from app.core import yaml_settings

class UserLoginRequest(BaseModel):
    username: str
    password: str

class LoginVerifyRequest(BaseModel):
    code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    access_token_expire_minutes: int = yaml_settings.JWT_TOKEN_EXPIRE_MINUTES
    refresh_token_expire_days: int = yaml_settings.REFRESH_TOKEN_EXPIRE_DAYS
