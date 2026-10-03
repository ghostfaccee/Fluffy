from typing import Optional

from fastapi import Request, APIRouter, Depends, status

from app.model import User
from app.schemas import UserResponse, UserRegister, UserUpdate, PasswordUpdate
from app.dependencies import get_user_service, get_current_user_uuid
from app.services import UserService

router = APIRouter(prefix = '/users', tags = ['users'])

@router.post('', response_model = UserResponse, status_code = status.HTTP_201_CREATED)
async def register(request: Request, data: UserRegister, service: UserService = Depends(get_user_service)) -> None:
    return await service.create(data)

@router.get('/me', response_model = UserResponse, status_code = status.HTTP_200_OK)
async def get_me(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> Optional[User]:
    return await service.get(current_user_uuid)

@router.get('/{username}', response_model = UserResponse, status_code = status.HTTP_200_OK)
async def get_another_user_by_username(request: Request, username: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> Optional[User]:
    return await service.get_by_username(username)

@router.patch('/me', response_model = UserResponse, status_code = status.HTTP_200_OK)
async def update_me(request: Request, data: UserUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> User:
    return await service.update(current_user_uuid, data)

@router.patch('/me/password', response_model = UserResponse, status_code = status.HTTP_200_OK)
async def update_my_password(request: Request, data: PasswordUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> User:
    return await service.update_password(current_user_uuid, data)

@router.delete('/me', status_code = status.HTTP_204_NO_CONTENT)
async def delete_me(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: UserService = Depends(get_user_service)) -> None:
    return await service.delete(current_user_uuid)
