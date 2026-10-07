from uuid import UUID
from sqlalchemy import select, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.model import Message

class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, message: Message) -> None:
        self.session.add(message)
    
    async def get_history(self, uuid_user_a: UUID, uuid_user_b: UUID, limit: int = 20, offset: int = 0) -> list[Message]:
        stmt = (
            select(Message).where(or_(
                and_(Message.sender_id == uuid_user_a, Message.receiver_id == uuid_user_b),
                and_(Message.sender_id == uuid_user_b, Message.receiver_id == uuid_user_a)
            )).order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
    
    async def mark_as_read(self, sender_uuid: UUID, receiver_uuid: UUID) -> int:
        stmt = (
            update(Message).where(
                Message.sender_id == sender_uuid,
                Message.receiver_id == receiver_uuid,
                Message.is_read == False
            )
            .values(is_read = True)
        )
        res = await self.session.execute(stmt)
        return res.rowcount
