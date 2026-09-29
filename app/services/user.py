import secrets
from uuid import UUID
from typing import Optional
from sqlalchemy.exc import IntegrityError

from app.exceptions import user as user_exc
from app.exceptions import redis as redis_exc
from app.repository import UnitOfWork, UserRepository
from app.model import User
from app.schemas import UserRegister, UserUpdate, PasswordUpdate
from app.utils import hash_password, verify_password
from app.infrastructure import TokenService, TokenServiceReturnValues, VerificationTokenService, VerificationTokenServiceReturnValues
from app.tasks.email import send_verification_email

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
        else:
            verification_token = secrets.token_urlsafe(32)
            status = await VerificationTokenService.store_verification_token(user.user_id, verification_token)
            if status is VerificationTokenServiceReturnValues.ERROR:
                raise redis_exc.InternalRedisError()
            send_verification_email.delay(user.email, verification_token)
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
        state = 'email' in update_data and update_data['email'] != user.email
        if state:
            user.is_active = False
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
        else:
            if state:
                verification_token = secrets.token_urlsafe(32)
                status = await VerificationTokenService.store_verification_token(user_id, verification_token)
                if status is VerificationTokenServiceReturnValues.ERROR:
                    raise redis_exc.InternalRedisError()
                send_verification_email.delay(update_data['email'], verification_token)
                await self._invalidate_token(user_id)
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
    