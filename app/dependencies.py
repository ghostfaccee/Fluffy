from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.repository import UnitOfWork
from app.services import UserService

async def get_uow(db: AsyncSession = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(db)

async def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow)

