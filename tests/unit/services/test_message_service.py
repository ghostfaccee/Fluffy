import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import uuid4

from app.services import message as message_module
from app.repository import UnitOfWork
from app.model import User, Message
from app.schemas import MessageCreate
from app.utils import hash_password
from app.exceptions import user as user_exc

# --- fixtures

@pytest.fixture
async def test_sender(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'sender',
        name = 'sender',
        email = 'sender@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_receiver(
    db_session: AsyncSession
) -> None:
    instance = User(
        username = 'receiver',
        name = 'receiver',
        email = 'receiver@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- send ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_but_receiver_doesnt_exists(
    db_session: AsyncSession,
    test_sender: User
) -> None:
    service = message_module.MessageService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.send(
            test_sender.user_id, 
            uuid4(), 
            MessageCreate(
                content = 'message'
            )
        )

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_success(
    db_session: AsyncSession,
    test_sender: User,
    test_receiver: User
) -> None:
    service = message_module.MessageService(UnitOfWork(db_session))
    res = await service.send(
        test_sender.user_id,
        test_receiver.user_id,
        MessageCreate(
            content = 'message'
        )
    )
    assert isinstance(res, Message)

# --- get history ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history_success(
    db_session: AsyncSession,
    test_sender: User,
    test_receiver: User
) -> None:
    service = message_module.MessageService(UnitOfWork(db_session))
    message = await service.send(
        test_sender.user_id,
        test_receiver.user_id,
        MessageCreate(
            content = 'message'
        )
    )
    messages = await service.get_history(test_sender.user_id, test_receiver.user_id)

    assert isinstance(messages, list)
    assert message in messages

# --- mark read ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mark_as_read_success(
    db_session: AsyncSession,
    test_sender: User,
    test_receiver: User
) -> None:
    service = message_module.MessageService(UnitOfWork(db_session))
    message = await service.send(
        test_sender.user_id,
        test_receiver.user_id,
        MessageCreate(
            content = 'message'
        )
    )
    message = await service.send(
        test_sender.user_id,
        test_receiver.user_id,
        MessageCreate(
            content = 'message'
        )
    )
    message = await service.send(
        test_sender.user_id,
        test_receiver.user_id,
        MessageCreate(
            content = 'message'
        )
    )
    count = await service.mark_read(test_sender.user_id, test_receiver.user_id)

    assert isinstance(count, int)
    assert count == 3
