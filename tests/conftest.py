import pytest
import pytest_asyncio

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from httpx import AsyncClient, ASGITransport

import os

from collections.abc import AsyncGenerator

from app.middleware import RateLimit
from app.core import Base
from app.core.database import get_db

RateLimit.disable_redis()

from app.main import app

TEST_DATABASE_URL = os.environ['POSTGRES_URL']

# When we spin up a Docker container for tests (using `--profile test`),
#  the URL for the test database is included in the environment variables
#  of the `testapi` Docker container. As a result,
#  we can successfully retrieve it as an environment variable using the `os` module.

database_name = make_url(TEST_DATABASE_URL).database

if not database_name or 'test' not in database_name.lower():
    raise RuntimeError(
        'Aborting test execution. The test database is either missing or is not a valid test database.' 
        'Please check the `docker-compose` environment variables for the `testapi` container.'
    )

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo = False,
    pool_pre_ping = True
)

TestSessionFactory = async_sessionmaker(
    bind = test_engine,
    expire_on_commit = False
)

@pytest_asyncio.fixture(scope = 'session', loop_scope = 'session', autouse = True)
async def prepare_db() -> AsyncGenerator[None, None]:
    '''
    Creates tables once for the entire session
    '''
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session(prepare_db: None) -> AsyncGenerator[AsyncSession, None]:
    '''
    Gives each test its own transaction
    '''
    async with test_engine.connect() as conn:
        transaction = await conn.begin()

        session_factory = async_sessionmaker(
            bind = conn,
            expire_on_commit = False,
            join_transaction_mode = 'create_savepoint'
            # join_transaction_mode - allows the application to trigger commits without terminating the external test transaction
        )

        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()

@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    '''
    Sends real ASGI requests to the test API
    '''
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app = app)

    async with AsyncClient(
        transport = transport,
        base_url = 'http://test'
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    # Changing the database connection
