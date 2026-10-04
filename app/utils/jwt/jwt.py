from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

from app.core import env_settings, yaml_settings

def create_access_token(data: dict, expires: int = yaml_settings.JWT_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes = expires)
    to_encode.update({'exp': expire, 'type': 'access'})
    return jwt.encode(to_encode, env_settings.SECRET_JWT_KEY, yaml_settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, env_settings.SECRET_JWT_KEY, yaml_settings.ALGORITHM)
        if payload.get('type') != 'access':
            return None
        return payload
    except JWTError:
        return None

def create_refresh_token(data: dict, expires: int = yaml_settings.REFRESH_TOKEN_EXPIRE_DAYS) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days = expires)
    to_encode.update({'exp': expire, 'type': 'refresh'})
    return jwt.encode(to_encode, env_settings.SECRET_REFRESH_KEY, yaml_settings.ALGORITHM)

def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, env_settings.SECRET_REFRESH_KEY, yaml_settings.ALGORITHM)
        if payload.get('type') != 'refresh':
            return None
        return payload
    except JWTError:
        return None
