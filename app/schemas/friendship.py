from uuid import UUID

from pydantic import BaseModel

class FriendshipResponse(BaseModel):
    user_low_id: UUID
    user_high_id: UUID
    requested_by: UUID
    status: str
