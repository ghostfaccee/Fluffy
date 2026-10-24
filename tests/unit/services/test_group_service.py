import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import uuid4

from app.model import User, Group, GroupMember
from app.services import group as group_module
from app.repository import UnitOfWork
from app.schemas import GroupCreate, GroupUpdate
from app.utils import hash_password
from app.exceptions import group as group_exc

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

# --- create ---

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

@pytest.mark.asyncio
async def test_get_group_and_member_but_group_not_found(
    db_session: AsyncSession
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.GroupNotFound):
        await service._get_group_and_member(uuid4(), uuid4())

@pytest.mark.asyncio
async def test_get_group_and_member_but_not_group_member(
    db_session: AsyncSession,
    test_group: Group
) -> None:
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NotGroupMember):
        await service._get_group_and_member(test_group.group_id, uuid4())

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

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('role'),
    [
        ('admin'),
        ('owner')
    ],
    ids = [
        'role_admin',
        'role_owner'
    ]
)
async def test_require_role_for_member(
    db_session: AsyncSession,
    test_user: User,
    test_group: Group,
    role: str
) -> None:
    test_user.role = 'member'
    await db_session.commit()
    service = group_module.GroupService(UnitOfWork(db_session))
    with pytest.raises(group_exc.NoPermissions):
        await service._require_role(test_user.user_id, role)
    