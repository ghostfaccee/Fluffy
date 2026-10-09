from uuid import UUID
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core import logger
from app.utils import decode_access_token
from app.infrastructure.websocket.manager import manager

router = APIRouter()

SUBPROTOCOL = 'fluffy'
BEARER_PREFIX = 'bearer.'

def _extract_token(ws: WebSocket) -> Optional[str]:
    protocols = ws.scope.get('subprotocols', [])
    for p in protocols:
        if p.startswith(BEARER_PREFIX):
            return p[len(BEARER_PREFIX):]
    return

@router.websocket('/ws')
async def websocket_endpoint(ws: WebSocket) -> None:
    token = _extract_token(ws)
    if not token:
        await ws.close(code = 1008)
        return
    payload = decode_access_token(token)
    if payload is None:
        await ws.close(code = 1008)
        return
    user_id = payload.get('sub')
    if user_id is None:
        await ws.close(code = 1008)
        return
    user_id = UUID(user_id)
    
    offered = ws.scope.get('subprotocols', [])
    accepted = SUBPROTOCOL if SUBPROTOCOL in offered else None
    await ws.accept(subprotocol = accepted)

    manager.connect(user_id, ws)

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, ws)
    except Exception as e:
        logger.error(f'WS error: {user_id}, {e}')
        manager.disconnect(user_id, ws)
