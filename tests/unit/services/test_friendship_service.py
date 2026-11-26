


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import User, Friendship
from app.repository import UnitOfWork
from app.utils import hash_password
from app.services import friendship as friendship_module
from app.exceptions import friendship as friendship_exc

# --- fixtures ---

@pytest.fixture
async def test_first_user(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'test_first_user',
        name = 'testuser',
        email = 'test_first_user@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_second_user(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'test_second_user',
        name = 'testuser',
        email = 'test_second_user@gmail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture()
async def test_friendship(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User
) -> Friendship:
    low_user_id, high_user_id = sorted([test_first_user.user_id, test_second_user.user_id])
    instance = Friendship(
        user_low_id = low_user_id,
        user_high_id = high_user_id,
        requested_by = test_first_user.user_id,
        status = 'pending'
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- create ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_success(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User
) -> None:
    service = friendship_module.FriendshipService(UnitOfWork(db_session))
    friendship = await service.create(test_first_user.user_id, test_second_user.user_id)
    assert isinstance(friendship, Friendship)

# --- accept ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_but_friendship_not_found(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User
) -> None:
    service = friendship_module.FriendshipService(UnitOfWork(db_session))
    with pytest.raises(friendship_exc.FriendshipDoesNotExists):
        await service.accept(test_first_user.user_id, test_second_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_but_sender_is_trying_accept_friendship(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User,
    test_friendship: Friendship
) -> None:
    service = friendship_module.FriendshipService(UnitOfWork(db_session))
    with pytest.raises(friendship_exc.SenderCannotAcceptFriendship):
        await service.accept(test_first_user.user_id, test_second_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_but_friendship_status_is_not_pending(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User,
    test_friendship: Friendship
) -> None:
    test_friendship.status = 'accepted'
    await db_session.commit()
    service = friendship_module.FriendshipService(UnitOfWork(db_session))
    with pytest.raises(friendship_exc.FriendshipIsNotPending):
        await service.accept(test_second_user.user_id, test_first_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_success(
    db_session: AsyncSession,
    test_first_user: User,
    test_second_user: User,
    test_friendship: Friendship
) -> None:
    service = friendship_module.FriendshipService(UnitOfWork(db_session))
    friendship = await service.accept(test_second_user.user_id, test_first_user.user_id)
    assert isinstance(friendship, Friendship)
    assert friendship.status == 'accepted'

# --- get_friendship_of_two_users ---

