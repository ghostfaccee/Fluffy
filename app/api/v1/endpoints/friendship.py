from uuid import UUID

from fastapi import APIRouter, Depends, status, Request

from app.middleware import RateLimit
from app.services import FriendshipService
from app.schemas import FriendshipResponse
from app.dependencies import get_current_user_uuid, get_frienship_service
from app.model import Friendship

router = APIRouter(prefix = '/friendships', tags = ['friends', 'friendships'])
limiter = RateLimit.get_limiter()

@router.post('/{user_id}', response_model = FriendshipResponse, status_code = status.HTTP_201_CREATED)
@limiter.limit('20/minute')
async def create_friendship(request: Request, user_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> Friendship:
    return await service.create(current_user_uuid, user_id)

@router.get('/{user_id}', response_model = FriendshipResponse, status_code = status.HTTP_200_OK)
@limiter.limit('20/minute')
async def get_friendship(request: Request, user_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> Friendship:
    return await service.get_friendship_of_two_users(current_user_uuid, user_id)

@router.get('/all/incoming', response_model = list[FriendshipResponse], status_code = status.HTTP_200_OK)
@limiter.limit('20/minute')
async def get_incoming_friendships(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> list[Friendship]:
    return await service.get_incoming_friendships(current_user_uuid)

@router.get('/all/outgoing', response_model = list[FriendshipResponse], status_code = status.HTTP_200_OK)
@limiter.limit('20/minute')
async def get_outgoing_friendships(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> list[Friendship]:
    return await service.get_outgoing_friendships(current_user_uuid)

@router.get('/all/accepted', response_model = list[FriendshipResponse], status_code = status.HTTP_200_OK)
@limiter.limit('20/minute')
async def get_all_accepted_friendships(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> list[Friendship]:
    return await service.get_all_accepted_friendships(current_user_uuid)

@router.patch('/accept/{user_id}', response_model = FriendshipResponse, status_code = status.HTTP_200_OK)
@limiter.limit('20/minute')
async def accept_friendship(request: Request, user_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> Friendship:
    return await service.accept(current_user_uuid, user_id)

@router.delete('/{user_id}', status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit('20/minute')
async def delete(request: Request, user_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: FriendshipService = Depends(get_frienship_service)) -> None:
    await service.delete(current_user_uuid, user_id)
