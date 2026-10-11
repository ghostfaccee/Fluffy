from app.schemas.user import UserRegister, UserUpdate, PasswordUpdate, UserResponse, AvatarSetRequest, AvatarUploadRequest, AvatarUploadResponse
from app.schemas.auth import UserLoginRequest, RefreshTokenRequest, TokenResponse, LoginVerifyRequest
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.group import GroupCreate, GroupMemberResponse, GroupMessageCreate, GroupMessageResponse
from app.schemas.group import GroupResponse, GroupUpdate

__all__ = [
    'UserRegister', 'UserUpdate', 'PasswordUpdate', 'UserLoginRequest',
    'RefreshTokenRequest', 'TokenResponse', 'LoginVerifyRequest',
    'UserResponse', 'AvatarSetRequest', 'AvatarUploadResponse', 'AvatarUploadRequest',
    'MessageCreate', 'MessageResponse', 'GroupCreate', 'GroupMemberResponse', 'GroupMessageCreate',
    'GroupMessageResponse', 'GroupResponse', 'GroupUpdate'
]
