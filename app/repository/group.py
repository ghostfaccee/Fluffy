from uuid import UUID
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import Group, GroupMember, GroupMessage

class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, group: Group) -> None:
        self.session.add(group)
    
    async def get(self, group_id: UUID) -> Optional[Group]:
        return await self.session.get(Group, group_id)
    
    async def get_by_invite_token(self, token: str) -> Optional[Group]:
        stmt = await self.session.execute(
            select(Group).where(Group.invite_token == token)
        )
        return stmt.scalar_one_or_none()
    
    async def delete(self, group: Group) -> None:
        await self.session.delete(group)
    
class GroupMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, group_member: GroupMember) -> None:
        self.session.add(group_member)
    
    async def get(self, group_id: UUID, user_id: UUID) -> Optional[GroupMember]:
        return await self.session.get(GroupMember, (group_id, user_id))
    
    async def delete(self, group_member: GroupMember) -> None:
        await self.session.delete(group_member)
    
    async def get_user_groups(self, user_id: UUID) -> list[Group]:
        stmt = (
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.group_id)
            .where(GroupMember.user_id == user_id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

class GroupMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, message: GroupMessage) -> None:
        self.session.add(message)
    
    async def get_history(
        self,
        group_id: UUID, 
        limit: int = 20,
        offset: int = 0
    ) -> list[GroupMessage]:
        stmt = (
            select(GroupMessage)
            .where(GroupMessage.group_id == group_id)
            .order_by(GroupMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
