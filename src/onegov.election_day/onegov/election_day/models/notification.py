from onegov.ballot.models import Election, Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from sqlalchemy import Text
from sqlalchemy import Column, ForeignKey
from uuid import uuid4


class Notification(Base, TimestampMixin):
    """ Stores triggered notifications. """

    __tablename__ = 'notifications'

    #: Identifies the notification
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The URL to call
    url = Column(Text, nullable=False)

    #: The corresponding election
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: The corresponding vote
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=True)

    #: The last update of the corresponding election/vote
    last_change = Column(UTCDateTime)
