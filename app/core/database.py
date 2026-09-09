from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core import env_settings, yaml_settings

engine = create_async_engine(url = env_settings.POSTGRES_URL, echo = yaml_settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(engine, class_ = AsyncSession, expire_on_commit = True)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
