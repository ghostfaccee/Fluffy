import yaml
from pydantic import ConfigDict, Field, BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

# === .env ===
class EnvSettings(BaseSettings):
    POSTGRES_URL: str

    REDIS_URL: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    model_config = ConfigDict(env_file = '.env', case_sensitive = True, extra = 'ignore')

env_settings = EnvSettings()

# === .yaml ===

class YamlSettings(BaseModel):
    DEBUG: bool
    SLOW_REQUEST_THRESHOLD: float
    VERIFICATION_LINK: str

    @classmethod
    def load(cls, yaml_path: str = 'config.yaml') -> YamlSettings:
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f'Config file not found: {yaml_path}')
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            return cls(**data)

yaml_settings = YamlSettings.load()