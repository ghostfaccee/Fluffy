import uuid


from sqlalchemy import CheckConstraint, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base

class Friendship(Base):
    __tablename__ = 'friendships'
    __table_args__ = (
        CheckConstraint('user_low_id < user_high_id', name = 'ck_friendship_order'),
        CheckConstraint(
            'requested_by IN (user_low_id, user_high_id)',
            name = 'ch_friendship_requester'
        ),
        CheckConstraint(
            'status IN (\'pending\', \'accepted\')',
            name = 'ck_friendship_status'
        ),
    )

    user_low_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey('users.user_id', ondelete = 'CASCADE'),
        primary_key = True
    )
    user_high_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey('users.user_id', ondelete = 'CASCADE'),
        primary_key = True
        # primary key is indexed automatically
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True))
    status: Mapped[str] = mapped_column(String(20), default = 'pending')
    # In the repository, we use a composite parameter in the `get` method query. There’s no need to add an index, though—Postgres creates one automatically.