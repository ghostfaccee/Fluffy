from uuid import UUID

from typing import Optional

from fastapi import Request, APIRouter, Depends, status

from app.model import User
from app.exceptions import user as user_exc
from app.schemas import UserResponse, UserRegister, UserUpdate, PasswordUpdate, AvatarUploadResponse, AvatarUploadRequest, AvatarSetRequest, PostResponse
from app.dependencies import get_user_service, get_current_user_uuid, get_post_service
from app.services import UserService, PostService
from app.utils.responses import build_user_response, build_post_response
from app.middleware import RateLimit
from app.infrastructure import CachingService

router = APIRouter(prefix = '/users', tags = ['users'])
limiter = RateLimit.get_limiter()

@router.post('', response_model = UserResponse, status_code = status.HTTP_201_CREATED)
@limiter.limit('10/minute')
async def register(request: Request, data: UserRegister, service: UserService = Depends(get_user_service)) -> User:
    return await service.create(data)

@router.get('/me', response_model = UserResponse, status_code = status.HTTP_200_OK)
@CachingService.cached(ttl = 30, namespace = 'users', user_id_field = 'current_user_uuid')
@limiter.limit('10/minute')
async def get_me(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.get(current_user_uuid)
    if user is None:
        raise user_exc.UserDoesNotExists()
    return await build_user_response(user)

@router.get('/{username}', response_model = UserResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_another_user_by_username(request: Request, username: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.get_by_username(username)
    if user is None:
        raise user_exc.UserDoesNotExists()
    return await build_user_response(user)

@router.patch('/me', response_model = UserResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def update_me(request: Request, data: UserUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.update(current_user_uuid, data)
    return await build_user_response(user)

@router.post('/me/avatar/upload-url', response_model = AvatarUploadResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_avatar_upload_url(request: Request, data: AvatarUploadRequest, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> AvatarUploadResponse:
    upload_url, key = await service.generate_avatar_upload_url(current_user_uuid, data.content_type)
    return AvatarUploadResponse(upload_url = upload_url, key = key)

@router.put('/me/avatar', response_model = UserResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def set_avatar(request: Request, data: AvatarSetRequest, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.set_avatar(current_user_uuid, data.key)
    return await build_user_response(user)

@router.delete('/me/avatar', status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit('10/minute')
async def delete_my_avatar(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> None:
    await service.delete_avatar(current_user_uuid)

@router.patch('/me/password', response_model = UserResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def update_my_password(request: Request, data: PasswordUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.update_password(current_user_uuid, data)
    return await build_user_response(user)

@router.delete('/me', status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit('10/minute')
async def delete_me(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> None:
    await service.delete(current_user_uuid)

# A user's posts belong to them, which is why the user's feed of posts can be found here.

@router.get('/{username}/posts', response_model = list[PostResponse], status_code = status.HTTP_200_OK)
@limiter.limit('25/minute')
async def user_posts(request: Request, username: str, limit: int = 20, offset: int = 0, current_user_uuid: UUID = Depends(get_current_user_uuid), service: PostService = Depends(get_post_service)) -> list[PostResponse]:
    posts = await service.get_user_posts(username, limit, offset)
    return [await build_post_response(p) for p in posts]
