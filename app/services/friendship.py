from uuid import UUID

from app.repository import UnitOfWork
from app.model import Friendship
from app.exceptions import user as user_exc
from app.exceptions import friendship as friendship_exc

class FriendshipService:

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def create(self, from_user_id: UUID, to_user_id: UUID) -> Friendship:
        low_user_id, high_user_id = await self._get_low_and_high_user_ids(from_user_id, to_user_id)
        friendship = Friendship(
            user_low_id = low_user_id,
            user_high_id = high_user_id,
            requested_by = from_user_id
        )
        self.uow.friendship.add(friendship)
        await self.uow.commit()
        return friendship
    
    async def accept(self, receiving_user_id: UUID, sending_user_id: UUID) -> Friendship:
        low_user_id, high_user_id = await self._get_low_and_high_user_ids(receiving_user_id, sending_user_id)
        friendship = await self.uow.friendship.get(low_user_id, high_user_id)
        if friendship is None:
            raise friendship_exc.FriendshipDoesNotExists()
        if friendship.requested_by != sending_user_id:
            raise friendship_exc.SenderCannotAcceptFriendship()
        if friendship.status != 'pending':
            raise friendship_exc.FriendshipIsNotPending()
        friendship.status = 'accepted'
        await self.uow.commit()
        return friendship
    
    async def get_friendship_of_two_users(self, first_user_id: UUID, second_user_id: UUID) -> Friendship:
        low_user_id, high_user_id = await self._get_low_and_high_user_ids(first_user_id, second_user_id)
        friendship = await self.uow.friendship.get(low_user_id, high_user_id)
        if friendship is None:
            raise friendship_exc.FriendshipDoesNotExists()
        return friendship
    
    async def get_incoming_friendships(self, user_id: UUID) -> list[Friendship]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        friendships = await self.uow.friendship.get_incoming(user_id)
        return friendships
    
    async def get_outgoing_friendships(self, user_id: UUID) -> list[Friendship]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        friendships = await self.uow.friendship.get_outgoing(user_id)
        return friendships

    async def get_all_accepted_friendships(self, user_id: UUID) -> list[Friendship]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        friendships = await self.uow.friendship.get_all_accepted(user_id)
        return friendships
    
    async def delete(self, first_user_id: UUID, second_user_id: UUID) -> None:
        # Either person—the one who sent the friend request or the one who accepted it—can remove the friendship.
        low_user_id, high_user_id = await self._get_low_and_high_user_ids(first_user_id, second_user_id)
        friendship = await self.uow.friendship.get(low_user_id, high_user_id)
        if friendship is None:
            raise friendship_exc.FriendshipDoesNotExists()
        await self.uow.friendship.delete(friendship)

    async def _get_low_and_high_user_ids(self, first_user_id: UUID, second_user_id: UUID) -> tuple[UUID, UUID]:
        first_user = await self.uow.user.get(first_user_id)
        if first_user is None:
            raise user_exc.UserDoesNotExists()
        second_user = await self.uow.user.get(second_user_id)
        if second_user is None:
            raise user_exc.UserDoesNotExists()
        low_user_id, high_user_id = sorted([first_user_id, second_user_id])
        return low_user_id, high_user_id
