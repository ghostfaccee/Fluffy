from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.model import User
from app.repository import UnitOfWork
from app.services import UserService
from app.services import AuthService
from app.utils import decode_access_token
from app.exceptions import auth as auth_exc

async def get_uow(db: AsyncSession = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(db)

async def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow)

async def get_auth_service(uow: UnitOfWork = Depends(get_uow)) -> AuthService:
    return AuthService(uow)

security = HTTPBearer()

async def get_current_user_uuid(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    uow: UnitOfWork = Depends(get_uow)
) -> UUID:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise auth_exc.InvalidAccessTokenError()
    user_id = payload.get('sub')
    if user_id is None:
        raise auth_exc.InvalidTokenError()
    return UUID(user_id)
