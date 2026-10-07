from uuid import UUID

from app.exceptions import user as user_exc
from app.repository import UnitOfWork
from app.schemas import MessageCreate
from app.model import Message

class MessageService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def send(self, sender_id: UUID, receiver_id: UUID, data: MessageCreate) -> Message:
        # TODO: Foreged Token: We also don't check the sender_id or the existence of the sender. But what if the token is forged?
        receiver = await self.uow.user.get(receiver_id)
        if not receiver:
            raise user_exc.UserDoesNotExists()
        
        message = Message(
            sender_id = sender_id,
            receiver_id = receiver_id,
            content = data.content
        )
        self.uow.message.add(message)
        await self.uow.commit()
        await self.uow.session.refresh(message)
        return message
    
    async def get_history(self, user_a_uuid: UUID, user_b_uuid: UUID, limit: int = 20, offset: int = 0) -> list[Message]:
        return await self.uow.message.get_history(user_a_uuid, user_b_uuid, limit, offset)
    
    async def mark_read(self, sender_id: UUID, receiver_id: UUID) -> int:
        count = await self.uow.message.mark_as_read(sender_id, receiver_id)
        await self.uow.commit()
        return count
