from sqlalchemy.ext.asyncio import AsyncSession
from app.repository import UserRepository

class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user = UserRepository(session)
    
    async def commit(self) -> None:
        await self.session.commit()
    
    async def rollback(self) -> None:
        await self.session.rollback()
