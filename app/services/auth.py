from uuid import UUID

from app.models import User
from app.repository import UnitOfWork
from app.schemas import UserLoginRequest, TokenResponse
from app.exceptions import auth as auth_exc
from app.exceptions import redis as redis_exc
from app.exceptions import user as user_exc
from app.exceptions import verification_token as verification_exc
from app.utils import verify_password, create_access_token, create_refresh_token, decode_refresh_token
from app.infrastructure import TokenService, TokenServiceReturnValues
from app.infrastructure import VerificationTokenService, VerificationTokenServiceReturnValues

class AuthService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def login(self, data: UserLoginRequest) -> TokenResponse:
        user = await self.uow.user.get_by_username(data.username)
        if user is None:
            raise auth_exc.InvalidUsername()
        if not verify_password(data.password, user.hashed_password):
            raise auth_exc.InvalidPassword()
        if not user.is_active:
            raise auth_exc.UserNotActive()
        access_token = create_access_token({'sub': str(user.user_id)})
        refresh_token = create_refresh_token({'sub': str(user.user_id)})
        status = await TokenService.store_refresh_token(user.user_id, refresh_token)
        if status is TokenServiceReturnValues.SUCCESS:
            return TokenResponse(
                access_token = access_token,
                refresh_token = refresh_token
            )
        else:
            raise redis_exc.InternalRedisError()
    
    async def logout(self, user_id: UUID) -> None:
        status = await TokenService.delete_refresh_token(user_id)
        if status is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        elif status is TokenServiceReturnValues.NOT_FOUND:
            raise auth_exc.TokenNotFound()
        else:
            return None
    
    async def verify_email(self, user_id: UUID, token: str) -> User:
        status = await VerificationTokenService.check_verification_token(user_id, token)
        if status is VerificationTokenServiceReturnValues.NOT_FOUND:
            raise verification_exc.VerificationTokenNotFoundError()
        if status is VerificationTokenServiceReturnValues.NOT_EQUAL:
            raise verification_exc.VerificationTokenNotEqualError()
        if status is VerificationTokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        
        if user.is_active:
            return user
        else:
            status = await VerificationTokenService.delete_verification_token(user_id)
            if status is VerificationTokenServiceReturnValues.ERROR:
                raise redis_exc.InternalRedisError()
            user.is_active = True
            await self.uow.commit()
            return user
    
    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise auth_exc.InvalidTokenError()
        user_id = payload.get('sub')
        if not user_id:
            raise auth_exc.InvalidTokenError()
        user_id = UUID(user_id)
        user = await self.uow.user.get(user_id)
        if user is None or not user.is_active:
            status = await TokenService.delete_refresh_token(user_id)
            if status is TokenServiceReturnValues.ERROR:
                raise redis_exc.InternalRedisError()
            raise auth_exc.UserNotActive()
        if await TokenService.in_blacklist(refresh_token) is TokenServiceReturnValues.SUCCESS:
            if await TokenService.delete_refresh_token(user_id) is TokenServiceReturnValues.ERROR:
                raise redis_exc.InternalRedisError()
            raise auth_exc.TokenInBlacklistError()
        stored = await TokenService.get_refresh_token(user_id)
        if stored is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        elif stored is TokenServiceReturnValues.NOT_FOUND:
            raise auth_exc.TokenNotFoundError()
        if stored != refresh_token:
            if await TokenService.delete_refresh_token(user_id) is TokenServiceReturnValues.ERROR:
                raise redis_exc.InternalRedisError()
            raise auth_exc.DifferentTokensError()
        new_access_token = create_access_token({'sub': str(user_id)})
        new_refresh_token = create_refresh_token({'sub': str(user_id)})
        if await TokenService.add_to_blacklist(refresh_token) is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        if await TokenService.store_refresh_token(user_id, new_refresh_token) is TokenServiceReturnValues.ERROR:
            raise redis_exc.InternalRedisError()
        return TokenResponse(
            access_token = new_access_token,
            refresh_token = new_refresh_token
        )
