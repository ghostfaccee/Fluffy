import secrets
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.model import Group, GroupMember, GroupMessage
from app.repository import UnitOfWork
from app.schemas import GroupCreate, GroupUpdate, GroupAvatarUploadUrlResponse, MessageCreate
from app.exceptions import group as group_exc
from app.exceptions import redis as redis_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.infrastructure import GroupAvatarUrlCacheService, s3_avatars, PubSubService

ROLE_RANK = {'member': 0, 'admin': 1, 'owner': 2}

class GroupService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    # === crud ===
    
    async def create(self, owner_id: UUID, data: GroupCreate) -> Group:
        group = Group(
            name = data.name,
            description = data.description,
            invite_token = secrets.token_urlsafe(32)
        )
        self.uow.group.add(group)
        await self.uow.session.flush()
        self.uow.group_member.add(
            GroupMember(
                group_id = group.group_id,
                user_id = owner_id,
                role = 'owner'
            )
        )
        await self.uow.commit()
        await self.uow.session.refresh(group)
        return group
    
    async def get(self, group_id: UUID, user_id: UUID) -> Group:
        group, _ = await self._get_group_and_member(group_id, user_id)
        return group
    
    async def get_user_groups(self, user_id: UUID) -> list[Group]:
        return await self.uow.group_member.get_user_groups(user_id)
    
    async def update(self, group_id: UUID, user_id: UUID, data: GroupUpdate) -> Group:
        group, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'admin')
        for k, v in data.model_dump(exclude_unset = True).items():
            setattr(group, k, v)
        await self.uow.commit()
        return group
    
    async def delete(self, group_id: UUID, user_id: UUID) -> None:
        group, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'owner')
        avatar_key = group.avatar_key
        await self.uow.group.delete(group)
        await self.uow.commit()
        await self._cleanup_avatar(group_id, avatar_key)
    
    # === helpers ===

    async def _get_group_and_member(self, group_id: UUID, user_id: UUID) -> tuple[Group, GroupMember]:
        group = await self.uow.group.get(group_id)
        if not group:
            raise group_exc.GroupNotFound()
        member = await self.uow.group_member.get(group_id, user_id)
        if not member:
            raise group_exc.NotGroupMember()
        return group, member
    
    def _require_role(self, member: GroupMember, min_role: str) -> None:
        if ROLE_RANK.get(member.role) < ROLE_RANK.get(min_role):
            raise group_exc.NoPermissions()
    
    async def _cleanup_avatar(self, group_id: UUID, old_key: str | None) -> None:
        status = await GroupAvatarUrlCacheService.delete_avatar(group_id)
        if not status:
            raise redis_exc.InternalRedisError()
        if old_key:
            status = await s3_avatars.delete_object(old_key)
            if not status:
                raise s3_storage_exc.S3InternalError()
    
    def _avatar_prefix(self, group_id: UUID) -> str:
        return f'avatars/group/{group_id}/'

    # === invite ===

    async def join(self, token: str, user_id: UUID) -> Group:
        group = await self.uow.group.get_by_invite_token(token)
        if not group:
            raise group_exc.GroupNotFound()
        if await self.uow.group_member.get(group.group_id, user_id):
            raise group_exc.AlreadyGroupMember()
        self.uow.group_member.add(GroupMember(
            group_id = group.group_id,
            user_id = user_id,
            role = 'member'
        ))
        try:
            await self.uow.commit()
        except IntegrityError:
            await self.uow.rollback()
            raise group_exc.AlreadyGroupMember()
        return group
    
    async def regenerate_group_token(self, group_id: UUID, user_id: UUID) -> Group:
        group, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'admin')
        group.invite_token = secrets.token_urlsafe(32)
        await self.uow.commit()
        return group
    
    # === members ===

    async def get_members(self, group_id: UUID, user_id: UUID) -> list[GroupMember]:
        await self._get_group_and_member(group_id, user_id)
        return await self.uow.group_member.get_members(group_id)
    
    async def update_role(self, group_id: UUID, actor_id: UUID, target_id: UUID, new_role: str) -> GroupMember:
        _, actor = await self._get_group_and_member(group_id, actor_id)
        self._require_role(actor, 'owner')
        target = await self.uow.group_member.get(group_id, target_id)
        if not target:
            raise group_exc.NotGroupMember()
        if target.user_id == actor.user_id:
            raise group_exc.NoPermissions()
        target.role = new_role
        await self.uow.commit()
        return target
    
    async def leave(self, group_id: UUID, user_id: UUID) -> None:
        _, member = await self._get_group_and_member(group_id, user_id)
        if member.role == 'owner':
            raise group_exc.OwnerCannotLeave()
        await self.uow.group_member.delete(member)
        await self.uow.commit()
    
    async def kick(self, group_id: UUID, actor_id: UUID, target_id: UUID) -> None:
        _, actor = await self._get_group_and_member(group_id, actor_id)
        self._require_role(actor, 'admin')
        target = await self.uow.group_member.get(group_id, target_id)
        if not target:
            raise group_exc.NotGroupMember()
        if ROLE_RANK[actor.role] <= ROLE_RANK[target.role]:
            raise group_exc.NoPermissions()
        await self.uow.group_member.delete(target)
        await self.uow.commit()
    
    # === avatars ===
    
    async def generate_avatar_upload_url(self, group_id: UUID, user_id: UUID, content_type: str) -> tuple[str, str]:
        _, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'admin')
        key = f'{self._avatar_prefix(group_id)}{uuid4()}.{'jpg' if content_type == 'image/jpeg' else 'png'}'
        upload_url = await s3_avatars.generate_presigned_put_url(key, content_type)
        return GroupAvatarUploadUrlResponse(
            upload_url = upload_url,
            key = key
        )
    
    async def set_avatar(self, group_id: UUID, user_id: UUID, key: str) -> Group:
        group, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'admin')
        old_key = group.avatar_key
        group.avatar_key = key
        await self.uow.commit()
        await self._cleanup_avatar(group_id, old_key)
        return group
    
    async def delete_avatar(self, group_id: UUID, user_id: UUID) -> None:
        group, member = await self._get_group_and_member(group_id, user_id)
        self._require_role(member, 'admin')
        old_key = group.avatar_key
        group.avatar_key = None
        await self.uow.commit()
        await self._cleanup_avatar(group_id, old_key)
    
class GroupMessageService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def _require_member(self, group_id: UUID, user_id: UUID) -> None:
        if not await self.uow.group.get(group_id):
            raise group_exc.GroupNotFound()
        if not await self.uow.group_member.get(group_id, user_id):
            raise group_exc.NotGroupMember()
    
    async def send(self, group_id: UUID, sender_id: UUID, data: MessageCreate) -> GroupMessage:
        await self._require_member(group_id, sender_id)
        message = GroupMessage(
            group_id = group_id,
            sender_id = sender_id,
            content = data.content
        )
        self.uow.group_message.add(message)
        await self.uow.commit()
        await self.uow.session.refresh(message)
        try:
            members_ids = await self.uow.group_member.get_members_ids(group_id)
            for member_id in members_ids:
                if member_id == sender_id: continue
                await PubSubService.publish_to_user(member_id, {
                    'type' : 'new_group_message',
                    'group_id' : str(group_id),
                    'message_id' : str(message.message_id),
                    'sender_id' : str(sender_id),
                    'content' : message.content,
                    'created_at' : message.created_at.isoformat()
                })
        except Exception as e:
            logger.error(f'Failed to publish user message {message.message_id}: {e}')
        return message
    
    async def get_history(self, group_id: UUID, user_id: UUID, limit: int = 20, offset: int = 0) -> list[GroupMessage]:
        await self._require_member(group_id, user_id)
        return await self.uow.group_message.get_history(group_id, limit, offset)
