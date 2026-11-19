from app.model import User, Group, GroupMessage, Message, Post
from app.schemas import UserResponse, MessageResponse, GroupResponse, GroupMessageResponse, PostResponse, StoryResponse
from app.infrastructure import AvatarUrlCacheService, GroupAvatarUrlCacheService, UserMusicCacheService, StoryMediaUrlCacheService
from app.exceptions import s3_storage as s3_storage_exc
from app.exceptions import story as story_exc

async def build_user_response(user: User) -> UserResponse:
    avatar_url = None
    music_url = None
    if user.avatar_key:
        avatar_url = await AvatarUrlCacheService.get_avatar(user.user_id, user.avatar_key)
        if avatar_url is None:
            raise s3_storage_exc.S3InternalError()
    if user.music_key:
        music_url = await UserMusicCacheService.get_music(user.user_id, user.music_key)
        if music_url is None:
            raise s3_storage_exc.S3InternalError()
    return UserResponse(
        user_id = user.user_id,
        name = user.name,
        username = user.username,
        email = user.email,
        bio = user.bio,

        avatar_url = avatar_url,
        music_url = music_url,

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

async def build_post_response(post: Post) -> PostResponse:
    author_response = await build_user_response(post.author)
    return PostResponse(
        # TODO: we have N+1 problem for redis: For 20 messages from the service,
        # resend 20 requests. It’s better to optimize later. (from build_user_response)
        post_id = post.post_id,
        title = post.title,
        content = post.content,
        created_at = post.created_at,
        author = author_response
    )

async def build_story_response(story: Story) -> StoryResponse:
    if story is None:
        raise story_exc.StoryNotFound()
    author_response = await build_user_response(story.author)
    media_url = await StoryMediaUrlCacheService.get_story_media(story.media_key)
    if media_url is None:
        raise s3_storage_exc.S3InternalError()
    return StoryResponse(
        # TODO: we have N+1 problem for redis: For 20 messages from the service,
        # resend 20 requests. It’s better to optimize later.
        story_id = story.story_id,
        title = story.title,
        media_url = media_url,
        created_at = story.created_at,
        expires_at = story.expires_at,
        author = author_response
    )