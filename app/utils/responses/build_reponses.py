from app.model import User
from app.schemas import UserResponse
from app.infrastructure import AvatarUrlCacheService
from app.exceptions import s3_storage as s3_storage_exc

async def build_user_response(user: User) -> UserResponse:
    avatar_url = None
    if user.avatar_key:
        avatar_url = await AvatarUrlCacheService.get_avatar(user.user_id, user.avatar_key)
        if avatar_url is None:
            raise s3_storage_exc.S3InternalError()
    return UserResponse(
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
