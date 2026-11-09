from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.model import Post

class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    def add(self, post: Post) -> None:
        self.session.add(post)
    
    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
    
    async def get(self, post_id: UUID) -> Post | None:
        return await self.session.get(Post, post_id)

    async def get_with_author(self, post_id: UUID) -> Post | None:
        stmt = (
            select(Post)
            .where(Post.post_id == post_id)
            .options(selectinload(Post.author))
        )
        return await self.session.scalar(stmt)

    async def get_user_posts(self, author_id: UUID, limit: int = 20, offset: int = 0) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .options(selectinload(Post.author))
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
    