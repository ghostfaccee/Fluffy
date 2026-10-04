import yaml
from pydantic import ConfigDict, BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

# === .env ===
class EnvSettings(BaseSettings):
    SECRET_JWT_KEY: str
    SECRET_REFRESH_KEY: str

    POSTGRES_URL: str
    RABBITMQ_URL: str

    REDIS_URL: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    S3_AVATARS_ENDPOINT_URL: str
    S3_AVATARS_ACCESS_KEY: str
    S3_AVATARS_SECRET_KEY: str
    S3_AVATARS_BUCKET_NAME: str
    S3_AVATARS_REGION: str
    model_config = ConfigDict(env_file = '.env', case_sensitive = True, extra = 'ignore')

env_settings = EnvSettings()

# === .yaml ===

class YamlSettings(BaseModel):
    JWT_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALGORITHM: str

    DEBUG: bool
    SLOW_REQUEST_THRESHOLD: float
    VERIFICATION_LINK: str
    LOGIN_CODE_LINK: str
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int
    LOGIN_CODE_EXPIRE_MINUTES: int

    AVATAR_PRESIGNED_PUT_URL_LIFETIME_MINUTES: int
    AVATAR_PRESIGNED_GET_URL_LIFETIME_MINUTES: int
    AVATAR_URL_CACHE_LIFETIME_MINUTES: int

    @classmethod
    def load(cls, yaml_path: str = 'config.yaml') -> YamlSettings:
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f'Config file not found: {yaml_path}')
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            return cls(**data)

yaml_settings = YamlSettings.load()