import time
from uuid import UUID

from fastapi import WebSocket

from app.core import logger, yaml_settings

class ConnectionManager:
    '''
    Local registry of WebSocket connections
        Connections reside in the processor's memory, 
        while Redis Pub/Sub is used for delivery between instances.

        Multi-device support is available. 
        A single user can maintain multiple connections.
    '''

    PING_TIMEOUT_SECONDS = 90

    def __init__(self):
        self._connections: dict[UUID, set[WebSocket]] = {}
        self._last_seen: dict[WebSocket, float] = {}
    
    async def connect(self, user_id: UUID, ws: WebSocket) -> None:
        conns = self._connections.setdefault(user_id, set())
        if len(conns) >= yaml_settings.MAX_WS_CONNECTIONS_PER_USER:
            oldest_ws = min(conns, key = lambda w: self._last_seen.get(w, 0))
            logger.warning(f'WS limit exceed for user: {user_id}, evicting oldest connection...')
            try:
                await oldest_ws.close(code = 1001)
            except Exception:
                pass
            conns.discard(oldest_ws)
            self._last_seen.pop(oldest_ws, None)
        conns.add(ws)
        self._last_seen[ws] = time.monotonic()
        logger.info(f'User {user_id} was connected. Total connections: {len(conns)}')
    
    def disconnect(self, user_id: UUID, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return None
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
        self._last_seen.pop(ws, None)
        logger.info(f'WS was disconnected for user {user_id}. Total connections: {len(conns)}')
    
    async def send_to_local(self, user_id: UUID, message: dict) -> int:
        conns = self._connections.get(user_id)
        if not conns:
            return 0
        dead: list[WebSocket] = []
        sent = 0
        for ws in list(conns):
            try:
                await ws.send_json(message)
                sent += 1
            except Exception as e:
                logger.error(f'WS send failed: {e}')
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)
        return sent
    
    def is_online(self, user_id: UUID) -> bool:
        return user_id in self._connections
    
    def touch(self, ws: WebSocket) -> None:
        self._last_seen[ws] = time.monotonic()
    
    def get_stale_connections(self) -> list[tuple[UUID, WebSocket]]:
        now = time.monotonic()
        stale: list[tuple[UUID, WebSocket]] = []
        for user_id, conns in self._connections.items():
            for ws in list(conns):
                last = self._last_seen.get(ws, 0)
                if now - last > self.PING_TIMEOUT_SECONDS:
                    stale.append((user_id, ws))
        return stale

manager = ConnectionManager()
