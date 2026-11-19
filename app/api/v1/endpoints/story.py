from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.middleware import RateLimit
from app.services import StoryService
from app.schemas import StoryUploadResponse, StoryUploadRequest, StoryResponse, StoryCreate
from app.dependencies import get_current_user_uuid, get_story_service
from app.utils.responses import build_story_response

router = APIRouter(prefix = '/stories', tags = ['stories'])
limiter = RateLimit.get_limiter()

@router.post('/upload-url', response_model = StoryUploadResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_story_upload_url(request: Request, data: StoryUploadRequest, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> StoryUploadResponse:
    upload_url, key = await service.generate_story_upload_url(current_user_uuid, data)
    return StoryUploadResponse(upload_url = upload_url, key = key)

@router.post('', response_model = StoryResponse, status_code = status.HTTP_201_CREATED)
@limiter.limit('10/minute')
async def create_story(request: Request, data: StoryCreate, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> StoryResponse:
    story = await service.create(current_user_uuid, data)
    return await build_story_response(story)

@router.get('/archive', response_model = list[StoryResponse], status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_archive(request: Request, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> list[StoryResponse]:
    stories = await service.get_all_author_stories(current_user_uuid)
    # For future reference: it would be a good idea to add a limit based and offset.
    return [await build_story_response(s) for s in stories]

@router.get('/archive/{story_id}', response_model = StoryResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_archive_story(request: Request, story_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> StoryResponse:
    story = await service.get_author_story(current_user_uuid, story_id)
    return await build_story_response(story)

@router.get('/{story_id}', response_model = StoryResponse, status_code = status.HTTP_200_OK)
@limiter.limit('10/minute')
async def get_active_story(request: Request, story_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> StoryResponse:
    story = await service.get_active_story_by_id(current_user_uuid, story_id)
    return await build_story_response(story)

@router.delete('/{story_id}', status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit('10/minute')
async def delete_story(request: Request, story_id: UUID, current_user_uuid: UUID = Depends(get_current_user_uuid), service: StoryService = Depends(get_story_service)) -> None:
    await service.delete(current_user_uuid, story_id)
