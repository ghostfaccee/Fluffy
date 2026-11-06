from sqlalchemy.ext.asyncio import AsyncSession
from app.repository import UserRepository, MessageRepository
from app.repository import GroupMemberRepository, GroupMessageRepository, GroupRepository

class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user = UserRepository(session)
        self.message = MessageRepository(session)
        self.group = GroupRepository(session)
        self.group_member = GroupMemberRepository(session)
        self.group_message = GroupMessageRepository(session)
    
    async def commit(self) -> None:
        await self.session.commit()
    
    async def rollback(self) -> None:
        await self.session.rollback()
