from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from onegov.activity.models import OccasionNeed
    from typing import Literal
    from typing import TypeAlias

    VolunteerState: TypeAlias = Literal[
        'open',
        'contacted',
        'confirmed',
    ]


class Volunteer(Base, ContentMixin, TimestampMixin):
    """ Describes a volunteer that has signed up to fulfill an
    occasion need.

    """

    __tablename__ = 'volunteers'

    #: The id of the record, may be used publicly
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The state of the volunteer
    state: Column[VolunteerState] = Column(
        Enum(  # type:ignore[arg-type]
            'open',
            'contacted',
            'confirmed',
            name='volunteer_state'
        ),
        nullable=False,
        default='open'
    )

    #: The need the volunteer signed up for
    need_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('occasion_needs.id'),
        nullable=False
    )
    need: relationship[OccasionNeed] = relationship(
        'OccasionNeed',
        back_populates='volunteers'
    )

    #: A token linking multiple volunteer records (volunteers sign up for
    #: multiple needs at once, and are then multiplexed here)
    token: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        nullable=False,
        default=uuid4
    )

    #: The first name of the volunteer
    first_name: Column[str] = Column(Text, nullable=False)

    #: The last name of the volunteer
    last_name: Column[str] = Column(Text, nullable=False)

    #: The address of the volunteer
    address: Column[str] = Column(Text, nullable=False)

    #: The zip code of the volunteer
    zip_code: Column[str] = Column(Text, nullable=False)

    #: The place of the volunteer
    place: Column[str] = Column(Text, nullable=False)

    #: The organisation of the volunteer
    organisation: Column[str | None] = Column(Text, nullable=True)

    #: The birth_date of the volunteer
    birth_date: Column[date] = Column(Date, nullable=False)

    #: The e-mail address of the volunteer
    email: Column[str] = Column(Text, nullable=False)

    #: The phone number of the volunteer
    phone: Column[str] = Column(Text, nullable=False)
