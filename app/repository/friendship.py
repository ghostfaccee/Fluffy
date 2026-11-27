
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.model import Friendship

class FriendshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, friendship: Friendship) -> None:
        self.session.add(friendship)
    
    async def get(self, low_user_id: UUID, high_user_id: UUID) -> Friendship | None:
        return await self.session.get(Friendship, (low_user_id, high_user_id))

    async def _get_list(self, user_id: UUID, status: str, *filtres) -> list[Friendship]:
        stmt = (
            select(Friendship)
            .where(
                or_(
                    Friendship.user_low_id == user_id,
                    Friendship.user_high_id == user_id
                ),
                Friendship.status == status,
                *filtres
            )
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
    
    async def get_incoming(self, user_id: UUID) -> list[Friendship]:
        return await self._get_list(user_id, 'pending', Friendship.requested_by != user_id)
    
    async def get_outgoing(self, user_id: UUID) -> list[Friendship]:
        return await self._get_list(user_id, 'pending', Friendship.requested_by == user_id)
    
    async def get_all_accepted(self, user_id: UUID) -> list[Friendship]:
        return await self._get_list(user_id, 'accepted')

    async def delete(self, friendship: Friendship) -> None:
        await self.session.delete(friendship)
