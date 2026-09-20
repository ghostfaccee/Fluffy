from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core import env_settings, yaml_settings

engine = create_async_engine(
    url = env_settings.POSTGRES_URL, 
    echo = yaml_settings.DEBUG,
    pool_pre_ping = True,
    pool_size = 10,
    max_overflow = 15,
    pool_recycle = 3600
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    expire_on_commit = False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
