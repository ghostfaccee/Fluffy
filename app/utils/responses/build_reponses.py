from app.model import User
from app.schemas import UserResponse, MessageResponse
from app.infrastructure import AvatarUrlCacheService
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
