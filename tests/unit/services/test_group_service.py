import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import uuid4
from unittest.mock import AsyncMock

from app.model import User, Group, GroupMember, GroupMessage
from app.services import group as group_module
from app.repository import UnitOfWork
from app.schemas import GroupCreate, GroupUpdate, GroupAvatarUploadUrlResponse, MessageCreate
from app.utils import hash_password
from app.exceptions import group as group_exc
from app.exceptions import redis as redis_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.infrastructure import GroupAvatarUrlCacheService, s3_avatars

# --- fixtures ---

@pytest.fixture
async def test_user(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'existing_user',
        name = 'testuser',
        email = 'email@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_group(
    db_session: AsyncSession,
    test_user: User
) -> None:
    group = await group_module.GroupService(UnitOfWork(db_session)).create(
        test_user.user_id,
        GroupCreate(
            name = 'test_group',
            description = 'test_desc'
        )
    )
    return group

@pytest.fixture
async def test_group_member(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> GroupMember:
    _, m = await group_module.GroupService(UnitOfWork(db_session))._get_group_and_member(test_group.group_id, test_user.user_id)
    return m

# --- create ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create(
    db_session: AsyncSession,
    test_user: User
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))

    res = await service.create(
        test_user.user_id, 
        GroupCreate(
            name = 'test_group',
            description = 'test'
        )
    )

    assert isinstance(res, Group)

# --- _get_group_and_member

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_group_and_member_but_group_not_found(
    db_session: AsyncSession
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.GroupNotFound):
        await service._get_group_and_member(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_group_and_member_but_not_group_member(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NotGroupMember):
        await service._get_group_and_member(test_group.group_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_group_and_member_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    g, m = await service._get_group_and_member(
        test_group.group_id, test_user.user_id
    )
    assert isinstance(g, Group)
    assert isinstance(m, GroupMember)

# --- get ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    g = await service.get(test_group.group_id, test_user.user_id)
    assert isinstance(g, Group)

# --- get_user_groups ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_groups_one_group(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    groups = await service.get_user_groups(test_user.user_id)
    assert test_group in groups
    assert isinstance(groups, list)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_groups_not_one(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    group = await service.create(
        test_user.user_id,
        GroupCreate(
            name = 'test_group2',
            description = 'test_desc2'
        )
    )
    groups = await service.get_user_groups(test_user.user_id)
    assert test_group in groups
    assert group in groups
    assert isinstance(groups, list)

# --- update ---

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('name', 'desc', 'vals'),
    [
        ('new_name', None, 1),
        ('new_name', 'new_desc', 2)
    ],
    ids = [
        'only_name',
        'name & desc (all)'
    ]
)
async def test_update_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    name: str,
    desc: str | None,
    vals: int
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    payload = {
        k: v for k, v in {
            'name': name,
            'description': desc
        }.items() if v is not None
    }
    group = await service.update(test_group.group_id, test_user.user_id, GroupUpdate(**payload))
    assert isinstance(group, Group)
    if vals < 2:
        assert group.description == test_group.description

# --- _require_role ---

@pytest.mark.unit
@pytest.mark.parametrize(
    ('rank', 'require_role'),
    [
        ('member', 'admin'),
        ('member', 'owner'),
        ('admin', 'owner')
    ],
    ids = [
        'member & admin',
        'member & owner',
        'admin & owner'
    ]
)
@pytest.mark.asyncio
async def test_require_role_with_no_permission(
    db_session: AsyncSession,
    test_group_member: GroupMember,
    rank: str,
    require_role: str
) -> None:
    test_group_member.role = rank
    await db_session.commit()

    service = group_module.GroupService(UnitOfWork(db_session))

    with pytest.raises(group_exc.NoPermissions):
        service._require_role(test_group_member, require_role)

@pytest.mark.unit
@pytest.mark.parametrize(
    ('rank', 'require_role'),
    [
        ('member', 'member'),
        ('admin', 'member'),
        ('admin', 'admin'),
        ('owner', 'admin'),
        ('owner', 'member'),
        ('owner', 'owner')
    ],
    ids = [
        'member & member',
        'admin & member',
        'admin & admin',
        'owner & admin',
        'owner & member',
        'owner & owner'
    ]
)
@pytest.mark.asyncio
async def test_require_role_success(
    db_session: AsyncSession,
    test_group_member: GroupMember,
    rank: str,
    require_role: str
) -> None:
    test_group_member.role = rank
    await db_session.commit()

    service = group_module.GroupService(UnitOfWork(db_session))

    service._require_role(test_group_member, require_role)

# _cleanup_avatar

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_avatar_without_old_key_with_internal_redis_error(
    db_session: AsyncSession,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = False)
    monkeypatch.setattr(GroupAvatarUrlCacheService, 'delete_avatar', delete_avatar)

    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service._cleanup_avatar(test_group.group_id, None)
    delete_avatar.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_avatar_with_old_key_but_s3_internal_error(
    db_session: AsyncSession,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = False)

    monkeypatch.setattr(GroupAvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(s3_storage_exc.S3InternalError):
        await service._cleanup_avatar(test_group.group_id, 'old_key ;)')
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_avatar_with_old_key_success(
    db_session: AsyncSession,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = True)

    monkeypatch.setattr(GroupAvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = group_module.GroupService(UnitOfWork(db_session))

    await service._cleanup_avatar(test_group.group_id, 'old key ;)')

    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_avatar_without_old_key_success(
    db_session: AsyncSession,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = True)

    monkeypatch.setattr(GroupAvatarUrlCacheService, 'delete_avatar', delete_avatar)

    service = group_module.GroupService(UnitOfWork(db_session))

    await service._cleanup_avatar(test_group.group_id, None)

    delete_avatar.assert_awaited_once()

# --- delete ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    cleanup_avatar = AsyncMock(return_value = None)

    monkeypatch.setattr(group_module.GroupService, '_cleanup_avatar', cleanup_avatar)

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.delete(test_group.group_id, test_user.user_id)

    cleanup_avatar.assert_awaited_once()

# --- join ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_join_but_group_not_found(
    db_session: AsyncSession,
    test_user: User
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.GroupNotFound):
        await service.join('unknown_token', test_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_join_but_user_already_group_member(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.AlreadyGroupMember):
        await service.join(test_group.invite_token, test_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_join_success(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    instance = User(
        username = 'iwantinyourgroup',
        name = ';)',
        email = 'myemail@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()


    service = group_module.GroupService(UnitOfWork(db_session))
    await service.join(test_group.invite_token, instance.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_join_with_integrity_error(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.AlreadyGroupMember):
        await service.join(test_group.invite_token, uuid4())

# --- regenerate group token ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_regenerate_group_token_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    old_token = test_group.invite_token
    new_token = (await service.regenerate_group_token(test_group.group_id, test_user.user_id)).invite_token
    assert old_token != new_token

# --- get members ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_members_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    res = await service.get_members(test_group.group_id, test_user.user_id)
    assert isinstance(res, list)
    assert res[0].user_id == test_user.user_id

# --- update role ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_role_but_target_is_not_group_member(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NotGroupMember):
        await service.update_role(test_group.group_id, test_user.user_id, uuid4(), 'admin')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_role_but_target_id_is_actor_id(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NoPermissions):
        await service.update_role(test_group.group_id, test_user.user_id, test_user.user_id, 'admin')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_role_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    instance = User(
        username = 'iwantinyourgroup',
        name = ';)',
        email = 'myemail@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.join(test_group.invite_token, instance.user_id)

    res = await service.update_role(test_group.group_id, test_user.user_id, instance.user_id, 'admin')
    assert isinstance(res, GroupMember)

# --- leave ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_leave_but_owner_cant_leave(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.OwnerCannotLeave):
        await service.leave(test_group.group_id, test_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_leave_success(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    instance = User(
        username = 'iwantinyourgroup',
        name = ';)',
        email = 'myemail@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.join(test_group.invite_token, instance.user_id)

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.leave(test_group.group_id, instance.user_id)

    groups = await service.get_user_groups(instance.user_id)
    assert len(groups) == 0

# --- kick ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_kick_but_target_is_not_group_member(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NotGroupMember):
        await service.kick(test_group.group_id, test_user.user_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_kick_but_no_permissions(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    instance = User(
        username = 'iwantinyourgroup',
        name = ';)',
        email = 'myemail@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.join(test_group.invite_token, instance.user_id)

    with pytest.raises(group_exc.NoPermissions):
        await service.kick(test_group.group_id, instance.user_id, test_user.user_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_kick_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    instance = User(
        username = 'iwantinyourgroup',
        name = ';)',
        email = 'myemail@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.join(test_group.invite_token, instance.user_id)

    await service.kick(test_group.group_id, test_user.user_id, instance.user_id)
    groups = await service.get_user_groups(instance.user_id)
    assert len(groups) == 0

# --- generate avatar upload url ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_avatar_upload_url_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    generate_presigned_put_url = AsyncMock(return_value = 'upload-url')
    monkeypatch.setattr(s3_avatars, 'generate_presigned_put_url', generate_presigned_put_url)

    service = group_module.GroupService(UnitOfWork(db_session))
    res = await service.generate_avatar_upload_url(test_group.group_id, test_user.user_id, 'png')
    assert isinstance(res, GroupAvatarUploadUrlResponse)

# --- set avatar ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_avatar_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    cleanup_avatar = AsyncMock(return_value = None)
    monkeypatch.setattr(group_module.GroupService, '_cleanup_avatar', cleanup_avatar)

    service = group_module.GroupService(UnitOfWork(db_session))
    res = await service.set_avatar(test_group.group_id, test_user.user_id, 'key')
    assert isinstance(res, Group)

# --- delete avatar ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_avatar(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    cleanup_avatar = AsyncMock(return_value = None)
    monkeypatch.setattr(group_module.GroupService, '_cleanup_avatar', cleanup_avatar)

    service = group_module.GroupService(UnitOfWork(db_session))
    await service.delete_avatar(test_group.group_id, test_user.user_id)
    assert test_group.avatar_key is None

# --- _require_member ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_member_but_group_not_found(
    db_session: AsyncSession
) -> None:
    service = group_module.GroupMessageService(UnitOfWork(db_session))
    with pytest.raises(group_exc.GroupNotFound):
        await service._require_member(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_member_but_user_not_group_member(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    service = group_module.GroupMessageService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NotGroupMember):
        await service._require_member(test_group.group_id, uuid4())

# --- send ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_success(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupMessageService(UnitOfWork(db_session))
    res = await service.send(test_group.group_id, 
        test_user.user_id, 
        MessageCreate(
            content = 'message'
        )
    )
    assert isinstance(res, GroupMessage)

# --- get history ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group
) -> None:
    service = group_module.GroupMessageService(UnitOfWork(db_session))
    message = await service.send(test_group.group_id, 
        test_user.user_id, 
        MessageCreate(
            content = 'message'
        )
    )
    messages = await service.get_history(test_group.group_id, test_user.user_id)

    assert isinstance(messages, list)
    assert message in messages
