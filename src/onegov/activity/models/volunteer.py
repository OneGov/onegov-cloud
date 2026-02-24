from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import OccasionNeed
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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The state of the volunteer
    state: Mapped[VolunteerState] = mapped_column(
        Enum(
            'open',
            'contacted',
            'confirmed',
            name='volunteer_state'
        ),
        default='open'
    )

    #: The need the volunteer signed up for
    need_id: Mapped[UUID] = mapped_column(ForeignKey('occasion_needs.id'))
    need: Mapped[OccasionNeed] = relationship(back_populates='volunteers')

    #: A token linking multiple volunteer records (volunteers sign up for
    #: multiple needs at once, and are then multiplexed here)
    token: Mapped[UUID] = mapped_column(default=uuid4)

    #: The first name of the volunteer
    first_name: Mapped[str]

    #: The last name of the volunteer
    last_name: Mapped[str]

    #: The address of the volunteer
    address: Mapped[str]

    #: The zip code of the volunteer
    zip_code: Mapped[str]

    #: The place of the volunteer
    place: Mapped[str]

    #: The organisation of the volunteer
    organisation: Mapped[str | None]

    #: The birth_date of the volunteer
    birth_date: Mapped[date]

    #: The e-mail address of the volunteer
    email: Mapped[str]

    #: The phone number of the volunteer
    phone: Mapped[str]
