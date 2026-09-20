from uuid import UUID
from typing import Optional
from sqlalchemy.exc import IntegrityError

from app.exceptions import user as user_exc
from app.exceptions import redis as redis_exc
from app.repository import UnitOfWork, UserRepository
from app.model import User
from app.schemas import UserRegister, UserUpdate, PasswordUpdate
from app.utils import hash_password, verify_password
from app.infrastructure import TokenService, TokenServiceReturnValues

class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def create(self, data: UserRegister) -> User:
        hashed_password = hash_password(data.password)
        user = User(
            name = data.name,
            username = data.username,
            email = data.email,
            bio = data.bio,

            city = data.city,
            university = data.university,
            institute = data.institute,
            group = data.group,

            hashed_password = hashed_password
        )
        self.uow.user.add(user)
        try:
            await self.uow.session.flush()
            await self.uow.session.refresh(user)
            await self.uow.commit()
        except IntegrityError as e:
            await self.uow.rollback()
            msg = str(e.orig).lower()
            if 'username' in msg:
                raise user_exc.UsernameAlreadyTaken()
            if 'email' in msg:
                raise user_exc.EmailAlreadyTaken()
            raise user_exc.UserAlreadyExists()
        return user
    
    async def get(self, user_id: UUID) -> Optional[User]:
        return await self.uow.user.get(user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.uow.user.get_by_username(username)
    
    async def update(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        update_data = data.model_dump(exclude_unset = True)
        if 'email' in update_data and update_data['email'] != user.email:
            # ---------
            user.is_active = False
            # ----------
            await self._invalidate_token(user_id)
        for key, value in update_data.items():
            setattr(user, key, value)
        try:
            await self.uow.commit()
        except IntegrityError as e:
            await self.uow.rollback()
            msg = str(e.orig).lower()
            if 'username' in msg:
                raise user_exc.UsernameAlreadyTaken()
            if 'email' in msg:
                raise user_exc.EmailAlreadyTaken()
            raise user_exc.UserAlreadyExists()
        return user
    
    async def update_password(self, user_id: UUID, data: PasswordUpdate) -> User:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        if not verify_password(data.old_password, user.hashed_password):
            raise user_exc.InvalidPassword()
        user.hashed_password = hash_password(data.new_password)
        await self._invalidate_token(user_id)
        await self.uow.commit()
        return user
    
    async def delete(self, user_id: UUID) -> None:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        await self.uow.user.delete(user)
        await self._invalidate_token(user_id)
        await self.uow.commit()

    async def _invalidate_token(self, user_id: UUID) -> bool:
        refresh_token = await TokenService.get_refresh_token(user_id)
        if refresh_token is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        if refresh_token is TokenServiceReturnValues.NOT_FOUND:
            return False
        status = await TokenService.add_to_blacklist(refresh_token)
        if status is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        return True
    