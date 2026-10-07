from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_message_service, get_current_user_uuid
from app.utils.responses import build_message_response
from app.schemas import MessageResponse, MessageCreate
from app.services import MessageService

router = APIRouter(prefix = '/messages', tags = ['messages'])

@router.post('/{receiver_id}', response_model = MessageResponse, status_code = status.HTTP_201_CREATED)
async def send_message(request: Request, receiver_id: UUID, data: MessageCreate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: MessageService = Depends(get_message_service)) -> MessageResponse:
    message = await service.send(current_user_uuid, receiver_id, data)
    return await build_message_response(message)

@router.get('/{other_user_id}', response_model = list[MessageResponse], status_code = status.HTTP_200_OK)
async def get_history(request: Request, other_user_id: UUID, limit: int = 20, offset: int = 0, current_user_uuid: UUID = Depends(get_current_user_uuid), service: MessageService = Depends(get_message_service)) -> list[MessageResponse]:
    messages = await service.get_history(current_user_uuid, other_user_id)
    # TODO: see app.utils.responses.build_responses.build_message_response
    return [await build_message_response(m) for m in messages]

@router.post('/{sender_id}/read', status_code = status.HTTP_200_OK)
async def mark_as_read(request: Request, sender_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: MessageService = Depends(get_message_service)) -> dict:
    count = await service.mark_read(sender_id, current_user_uuid)
    return {'marked_as_read': count}
