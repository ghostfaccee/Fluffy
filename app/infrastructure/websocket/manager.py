from uuid import UUID

from fastapi import WebSocket

from app.core import logger

class ConnectionManager:
    '''
    Local registry of WebSocket connections
        Connections reside in the processor's memory, 
        while Redis Pub/Sub is used for delivery between instances.

        Multi-device support is available. 
        A single user can maintain multiple connections.
    '''

    def __init__(self):
        self._connections: dict[UUID, set[WebSocket]] = {}
    
    def connect(self, user_id: UUID, ws: WebSocket) -> None:
        self._connections.setdefault(user_id, set()).add(ws)
        logger.info(f'User {user_id} was connected. Total connections: {len(self._connections)}')
    
    def disconnect(self, user_id: UUID, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return None
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
        logger.info(f'WS was disconnected for user {user_id}. Total connections: {len(self._connections)}')
    
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

manager = ConnectionManager()
