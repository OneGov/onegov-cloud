from onegov.ballot.models import Election, Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from sqlalchemy import Text
from sqlalchemy import Column, ForeignKey
from uuid import uuid4


class Webhook(Base, TimestampMixin):
    """ tbd """

    __tablename__ = 'webhooks'

    id = Column(UUID, primary_key=True, default=uuid4)

    url = Column(Text, nullable=False)

    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    vote_id = Column(Text, ForeignKey(Vote.id), nullable=True)

    last_change = Column(UTCDateTime)
