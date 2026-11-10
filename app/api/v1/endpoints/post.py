from uuid import UUID

from fastapi import APIRouter, Depends, status, Request

from app.middleware import RateLimit
from app.schemas import PostResponse, PostCreate, PostUpdate
from app.dependencies import get_current_user_uuid, get_post_service
from app.services import PostService
from app.utils.responses import build_post_response

router = APIRouter(prefix = '/posts', tags = ['posts'])
limiter = RateLimit.get_limiter()

@router.post('', response_model = PostResponse, status_code = status.HTTP_201_CREATED)
@limiter.limit('15/minute')
async def create_post(request: Request, data: PostCreate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: PostService = Depends(get_post_service)) -> PostResponse:
    post = await service.create(current_user_uuid, data)
    return await build_post_response(post)

# consider adding caching
@router.get('/{post_id}', response_model = PostResponse, status_code = status.HTTP_200_OK)
@limiter.limit('15/minute')
async def get_post(request: Request, post_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: PostService = Depends(get_post_service)) -> PostResponse:
    post = await service.get(current_user_uuid, post_id)
    return await build_post_response(post)

@router.patch('/{post_id}', response_model = PostResponse, status_code = status.HTTP_200_OK)
@limiter.limit('15/minute')
async def update_post(request: Request, post_id: UUID, data: PostUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: PostService = Depends(get_post_service)) -> PostResponse:
    post = await service.update(current_user_uuid, post_id, data)
    return await build_post_response(post)

@router.delete('/{post_id}', status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit('15/minute')
async def delete_post(request: Request, post_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: PostService = Depends(get_post_service)) -> None:
    await service.delete(current_user_uuid, post_id)
