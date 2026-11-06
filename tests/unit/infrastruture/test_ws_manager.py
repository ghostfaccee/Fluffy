import pytest

from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4, UUID

from app.infrastructure.websocket.manager import ConnectionManager

# --- fixtures ---

@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()

@pytest.fixture
def rand_uuid() -> UUID:
    return uuid4()

@pytest.fixture
def ws() -> MagicMock:
    ws = MagicMock()
    return ws

# --- connect ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_one_device_sucess(
    manager: ConnectionManager,
    rand_uuid: UUID,
    ws: MagicMock
) -> None:
    await manager.connect(rand_uuid, ws)

    assert manager.is_online(rand_uuid)
    assert ws in manager._connections[rand_uuid]
    assert ws in manager._last_seen

@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_support_multidevice_success(
    manager: ConnectionManager,
    rand_uuid: UUID
) -> None:
    ws1 = MagicMock()
    ws2 = MagicMock()

    await manager.connect(rand_uuid, ws1)
    await manager.connect(rand_uuid, ws2)

    assert len(manager._connections[rand_uuid]) == 2

# --- disconnect ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_success(
    manager: ConnectionManager,
    rand_uuid: UUID,
    ws: MagicMock
) -> None:
    await manager.connect(rand_uuid, ws)

    manager.disconnect(rand_uuid, ws)

    assert not manager.is_online(rand_uuid)
    assert ws not in manager._connections

@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_not_kill_other_connection(
    manager: ConnectionManager,
    rand_uuid: UUID
) -> None:
    ws1 = MagicMock()
    ws2 = MagicMock()

    await manager.connect(rand_uuid, ws1)
    await manager.connect(rand_uuid, ws2)

    manager.disconnect(rand_uuid, ws1)

    assert manager.is_online(rand_uuid)
    assert ws2 in manager._connections[rand_uuid]
    assert ws1 not in manager._connections[rand_uuid]

# --- send to local ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_to_local_success(
    manager: ConnectionManager,
    rand_uuid: UUID
) -> None:
    ws1 = MagicMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock
    ws2.send_json = AsyncMock()

    await manager.connect(rand_uuid, ws1)
    await manager.connect(rand_uuid, ws2)

    msg = {'content': 'hi'}

    sent = await manager.send_to_local(rand_uuid, msg)

    assert sent == 2
    ws1.send_json.assert_awaited_once_with(msg)
    ws2.send_json.assert_awaited_once_with(msg)
