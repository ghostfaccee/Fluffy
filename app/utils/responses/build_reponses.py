from app.model import User, Group, GroupMessage
from app.schemas import UserResponse, MessageResponse, GroupResponse, GroupMessageResponse
from app.infrastructure import AvatarUrlCacheService, GroupAvatarUrlCacheService
from app.exceptions import s3_storage as s3_storage_exc

async def build_user_response(user: User) -> UserResponse:
    avatar_url = None
    if user.avatar_key:
        avatar_url = await AvatarUrlCacheService.get_avatar(user.user_id, user.avatar_key)
        if avatar_url is None:
            raise s3_storage_exc.S3InternalError()
    return UserResponse(
        user_id = user.user_id,
        name = user.name,
        username = user.username,
        email = user.email,
        bio = user.bio,
        avatar_url = avatar_url,

        city = user.city,
        university = user.university,
        institute = user.institute,
        group = user.group
    )

async def build_message_response(message: Message) -> MessageResponse:
    sender_response = await build_user_response(message.sender)
    return MessageResponse(
        # TODO: we have N+1 problem for redis: For 20 messages from the service,
        # resend 20 requests. It’s better to optimize later.
        message_id = message.message_id,
        sender_id = message.sender_id,
        content = message.content,
        is_read = message.is_read,
        created_at = message.created_at,
        sender = sender_response
    )

async def build_group_response(group: Group) -> GroupResponse:
    avatar_url = None
    if group.avatar_key:
        avatar_url = await GroupAvatarUrlCacheService.get_avatar(group.group_id, group.avatar_key)
        if avatar_url is None:
            raise s3_storage_exc.S3InternalError()
    return GroupResponse(
        group_id = group.group_id,
        name = group.name,
        description = group.description,
        avatar_url = avatar_url,
        invite_token = group.invite_token,
        created_at = group.created_at
    )

async def build_group_message_response(message: GroupMessage) -> GroupMessageResponse:
    sender_response = await build_user_response(message.sender)
    return GroupMessageResponse(
        # TODO: we have N+1 problem for redis: For 20 messages from the service,
        # resend 20 requests. It’s better to optimize later.
        message_id = message.message_id,
        group_id = message.group_id,
        sender_id = message.sender_id,
        content = message.content,
        created_at = message.created_at,
        sender = sender_response
    )
