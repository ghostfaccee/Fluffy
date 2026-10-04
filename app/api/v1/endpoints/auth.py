from uuid import UUID

from fastapi import Depends, APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.middleware.rate_limit import RateLimit
from app.model import User
from app.schemas import UserLoginRequest, TokenResponse, LoginVerifyRequest, RefreshTokenRequest
from app.services import AuthService
from app.dependencies import get_auth_service, get_current_user_uuid

router = APIRouter(prefix = '/auth', tags = ['auth'])
limiter = RateLimit.get_limiter()

@router.post('/login', status_code = status.HTTP_202_ACCEPTED)
async def login(request: Request, data: UserLoginRequest, service: AuthService = Depends(get_auth_service)) -> JSONResponse:
    await service.login(data)
    return {'detail': 'A confirmation code has been sent to your email.'}

@router.post('/login/verify/{username}', response_model = TokenResponse, status_code = status.HTTP_200_OK)
async def verify_login(request: Request, username: str, data: LoginVerifyRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.verify_login_code(data, username)

@router.post('/logout', status_code = status.HTTP_204_NO_CONTENT)
async def logout(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: AuthService = Depends(get_auth_service)) -> None:
    await service.logout(current_user_uuid)

@router.post('/refresh', response_model = TokenResponse, status_code = status.HTTP_200_OK)
async def refresh(request: Request, data: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.refresh(data.refresh_token)

@router.post('/verify', status_code = status.HTTP_200_OK)
async def verify_email(request: Request, user_id: str, token: str, service: AuthService = Depends(get_auth_service)) -> JSONResponse:
    await service.verify_email(UUID(user_id), token)
    return {'detail': 'Your email has been successfully verified.'}

