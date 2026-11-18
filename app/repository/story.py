from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.model import Story

class StoryRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session
    
    def add(self, story: Story) -> None:
        self.session.add(story)
    
    async def delete(self, story: Story) -> None:
        await self.session.delete(story)

    async def get_active_by_id(self, story_id: UUID) -> Story | None:
        stmt = (
            select(Story).where(
                Story.story_id == story_id,
                Story.expires_at > func.now()
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
    
    async def get_active_stories_by_author_id(self, author_id: UUID) -> list[Story]:
        stmt = (
            select(Story)
            .where(
                Story.author_id == author_id,
                Story.expires_at > func.now()
            )
            .order_by(Story.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
    
    async def get_count_of_user_active_stories(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Story)
            .where(
                Story.author_id == user_id,
                Story.expires_at > func.now()
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def get_all_stories_by_author_id(self, author_id: UUID) -> list[Story]:
        stmt = (
            select(Story)
            .where(
                Story.author_id == author_id
            )
            .order_by(Story.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_story(self, story_id: UUID) -> Story | None:
        return await self.session.get(Story, story_id)
