from app.repository import UnitOfWork
from app.schemas import PostCreate, PostUpdate
from app.exceptions import user as user_exc
from app.exceptions import post as post_exc
from app.model import Post, User

class PostService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    # --- crud ---
    
    async def create(self, author_id: UUID, data: PostCreate) -> Post:
        author = await self.uow.user.get(author_id)
        if author is None:
            raise user_exc.UserDoesNotExists()
        post = Post(
            author_id = author_id,
            title = data.title,
            content = data.content
        )
        post.author = author
        self.uow.post.add(post)
        await self.uow.commit()
        return post
    
    async def get_user_posts(self, username: str, limit: int, offset: int) -> list[Post]:
        author = await self.uow.user.get_by_username(username)
        if author is None:
            raise user_exc.UserDoesNotExists()
        return await self.uow.post.get_user_posts(author.user_id, limit, offset)
    
    async def get(self, user_id: UUID, post_id: UUID) -> Post:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        post = await self.uow.post.get_with_author(post_id)
        if post is None:
            raise post_exc.PostDoesNotExists()
        return post
    
    async def delete(self, user_id: UUID, post_id: UUID) -> None:
        user, post = await self._get_user_and_post(user_id, post_id)
        await self._is_author(user, post)
        await self.uow.post.delete(post)
        await self.uow.commit()
    
    async def update(self, user_id: UUID, post_id: UUID, data: PostUpdate) -> Post:
        user, post = await self._get_user_and_post(user_id, post_id)
        await self._is_author(user, post)
        update_data = data.model_dump(exclude_unset = True, exclude_none = True)
        for key, value in update_data.items():
            setattr(post, key, value)
        post.author = user
        await self.uow.commit()
        return post
    
    # --- helpers ---
    
    async def _get_user_and_post(self, user_id: UUID, post_id: UUID) -> tuple[User, Post]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        post = await self.uow.post.get(post_id)
        if post is None:
            raise post_exc.PostDoesNotExists()
        return user, post

    async def _is_author(self, user: User, post: Post) -> None:
        if user.user_id != post.author_id:
            raise post_exc.AccessDenied()
    