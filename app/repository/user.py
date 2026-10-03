from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.model import User
from typing import Optional
from uuid import UUID

class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, user: User) -> None:
        self.session.add(user)
    
    async def delete(self, user: User) -> None:
        await self.session.delete(user)
    
    async def get(self, user_id: UUID) -> Optional[User]:
        return await self.session.get(User, user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
