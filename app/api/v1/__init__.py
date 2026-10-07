from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.message import router as message_router

router = APIRouter()

@router.get('/')
async def main_page():
    return {'detail': 'Welcome to Fluffy'}

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(message_router)