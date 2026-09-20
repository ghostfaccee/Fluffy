
from app.repository import UnitOfWork
from app.schemas import UserLoginRequest

class AuthService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def login(self, data: UserLoginRequest) -> TokenResponse:
        user = await self.uow.user.get_by_username(data.username)
        ##########