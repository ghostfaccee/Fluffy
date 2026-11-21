from __future__ import annotations

import yaml
from pydantic import ConfigDict, BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

# === .env ===
class EnvSettings(BaseSettings):
    SECRET_JWT_KEY: str
    SECRET_REFRESH_KEY: str

    POSTGRES_URL: str

    REDIS_URL: str

    RABBITMQ_URL: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    S3_SERVICE_ENDPOINT_URL: str | None = None
    S3_SERVICE_ACCESS_KEY: str | None = None
    S3_SERVICE_SECRET_KEY: str | None = None
    S3_SERVICE_BUCKET_NAME: str | None = None
    S3_SERVICE_REGION: str | None = None

    model_config = ConfigDict(env_file = '.env', case_sensitive = True, extra = 'ignore')

env_settings = EnvSettings()

# === .yaml ===

class YamlSettings(BaseModel):
    DEBUG: bool
    SLOW_REQUEST_THRESHOLD: float

    CACHING_DEFAULT_TTL: int

    VERIFICATION_LINK: str

    VERIFICATION_TOKEN_EXPIRE_MINUTES: int
    LOGIN_CODE_EXPIRE_MINUTES: int

    JWT_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALGORITHM: str

    DEFAULT_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    DEFAULT_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    DEFAULT_CACHE_LIFETIME_MINUTES: int

    AVATAR_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    AVATAR_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    AVATAR_URL_CACHE_LIFETIME_MINUTES: int

    GROUP_AVATAR_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    GROUP_AVATAR_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    GROUP_AVATAR_URL_CACHE_LIFETIME_MINUTES: int

    USER_MUSIC_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    USER_MUSIC_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    USER_MUSIC_CACHE_LIFETIME_MINUTES: int

    STORY_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    STORY_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    STORY_CACHE_LIFETIME_MINUTES: int

    POST_MEDIA_PRESIGNED_PUT_URL_LIFETINE_MINUTES: int
    POST_MEDIA_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    POST_MEDIA_CACHE_LIFETIME_MINUTES: int

    MAX_WS_CONNECTIONS_PER_USER: int

    USER_AVATAR_KEY: str
    USER_MUSIC_KEY: str
    GROUP_AVATAR_KEY: str
    STORY_KEY: str
    POST_MEDIA_KEY: str

    @classmethod
    def load(cls, yaml_path: str = 'config.yaml') -> YamlSettings:
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f'Config file not found: {yaml_path}')
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            return cls(**data)

yaml_settings = YamlSettings.load()
