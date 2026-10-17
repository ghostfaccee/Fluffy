from uuid import UUID

from fastapi import APIRouter, Depends, status, Request

from app.model import GroupMessage, GroupMember
from app.schemas import (
    GroupCreate, GroupUpdate, GroupResponse,
    GroupMessageResponse, GroupMessageCreate, GroupMemberResponse, GroupAvatarUploadUrlResponse,
    GroupAvatarUploadRequest, GroupAvatarSetRequest, GroupMemberRoleUpdate
)
from app.dependencies import get_group_message_service, get_group_service, get_current_user_uuid
from app.services import GroupMessageService, GroupService
from app.utils.responses import build_group_response, build_group_message_response

router = APIRouter(prefix = '/groups', tags = ['groups'])

# === group ===

@router.post('', response_model = GroupResponse, status_code = status.HTTP_201_CREATED)
async def create_group(request: Request, data: GroupCreate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.create(current_user_uuid, data)
    return await build_group_response(group)

@router.get('', response_model = list[GroupResponse], status_code = status.HTTP_200_OK)
async def get_user_groups(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> list[GroupResponse]:
    groups = await service.get_user_groups(current_user_uuid)
    return [await build_group_response(g) for g in groups]

@router.post('/join/{invite_token}', response_model = GroupResponse, status_code = status.HTTP_200_OK)
async def join_group(request: Request, invite_token: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.join(invite_token, current_user_uuid)
    return await build_group_response(group)

@router.get('/{group_id}', response_model = GroupResponse, status_code = status.HTTP_200_OK)
async def get_group(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.get(UUID(group_id), current_user_uuid)
    return await build_group_response(group)

@router.patch('/{group_id}', response_model = GroupResponse, status_code = status.HTTP_200_OK)
async def update_group(request: Request, group_id: str, data: GroupUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.update(UUID(group_id), current_user_uuid, data)
    return await build_group_response(group)

@router.delete('/{group_id}', status_code = status.HTTP_204_NO_CONTENT)
async def delete_group(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> None:
    await service.delete(UUID(group_id), current_user_uuid)

@router.post('/{group_id}/invite-token', response_model = GroupResponse, status_code = status.HTTP_200_OK)
async def regenerate_invite_token(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.regenerate_group_token(UUID(group_id), current_user_uuid)
    return await build_group_response(group)

# === avatar ===

@router.post('/{group_id}/avatar/upload-url', response_model = GroupAvatarUploadUrlResponse, status_code = status.HTTP_200_OK)
async def avatar_upload_url(request: Request, group_id: str, data: GroupAvatarUploadRequest, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupAvatarUploadUrlResponse:
    return await service.generate_avatar_upload_url(UUID(group_id), current_user_uuid, data.content_type)

@router.put('/{group_id}/avatar', response_model = GroupResponse, status_code = status.HTTP_200_OK)
async def set_group_avatar(request: Request, group_id: str, data: GroupAvatarSetRequest, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupResponse:
    group = await service.set_avatar(UUID(group_id), current_user_uuid, data.key)
    return await build_group_response(group)

@router.delete('/{group_id}/avatar', status_code = status.HTTP_204_NO_CONTENT)
async def delete_group_avatar(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> None:
    await service.delete_avatar(UUID(group_id), current_user_uuid)

# === members ===

@router.get('/{group_id}/members', response_model = list[GroupMemberResponse], status_code = status.HTTP_200_OK)
async def get_group_members(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> list[GroupMemberResponse]:
    members = await service.get_members(UUID(group_id), current_user_uuid)
    return [m for m in members]

@router.delete('/{group_id}/members/me', status_code = status.HTTP_204_NO_CONTENT)
async def leave_group(request: Request, group_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> None:
    await service.leave(UUID(group_id), current_user_uuid)

@router.delete('/{group_id}/members/{user_id}', status_code = status.HTTP_204_NO_CONTENT)
async def kick_group_member(request: Request, group_id: str, user_id: str, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> None:
    await service.kick(UUID(group_id), current_user_uuid, UUID(user_id))

@router.patch('/{group_id}/members/{user_id}/change-role', response_model = GroupMemberResponse, status_code = status.HTTP_200_OK)
async def update_role(request: Request, group_id: str, user_id: str, data: GroupMemberRoleUpdate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupService = Depends(get_group_service)) -> GroupMember:
    return await service.update_role(UUID(group_id), current_user_uuid, UUID(user_id), data.role)

# === messages ===

@router.post('/{group_id}/messages', response_model = GroupMessageResponse, status_code = status.HTTP_200_OK)
async def send_message(request: Request, group_id: str, data: GroupMessageCreate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupMessageService = Depends(get_group_message_service)) -> GroupMessage:
    message = await service.send(UUID(group_id), current_user_uuid, data)
    return await build_group_message_response(message)

@router.get('/{group_id}/messages', response_model = list[GroupMessageResponse], status_code = status.HTTP_200_OK)
async def get_message_history(request: Request, group_id: str, limit: int = 20, offset: int = 0, current_user_uuid: UUID = Depends(get_current_user_uuid), service: GroupMessageService = Depends(get_group_message_service)) -> list[GroupMessageResponse]:
    messages = await service.get_history(UUID(group_id), current_user_uuid, limit, offset)
    return [await build_group_message_response(m) for m in messages]
