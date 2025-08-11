from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from .activity import Activity
    from .period import BookingPeriod


class PublicationRequest(Base, TimestampMixin):
    """ Describes a request for publication. As users create new activities
    they need to ask for publication, where the activity is reviewed before
    it is made public.

    This repeats each period. Every activity which should be provided again
    has to be requested again. This is even possible multiple times per
    period, though that should be the exception.

    """

    __tablename__ = 'publication_requests'

    #: The public id of the publication request
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The activity linked to this request
    activity_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('activities.id'),
        nullable=False
    )
    activity: relationship[Activity] = relationship(
        'Activity',
        back_populates='publication_requests',
        lazy='joined'
    )

    #: The period linked to this request
    period_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('periods.id'),
        nullable=False
    )
    period: relationship[BookingPeriod] = relationship(
        'BookingPeriod',
        back_populates='publication_requests',
        lazy='joined'
    )
