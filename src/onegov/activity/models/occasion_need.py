from __future__ import annotations

from onegov.activity.types import BoundedIntegerRange
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .occasion import Occasion
    from .volunteer import Volunteer


class OccasionNeed(Base, TimestampMixin):
    """ Defines a required resource on an occasion. """

    __tablename__ = 'occasion_needs'

    #: the public id of this occasion resource
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the name of the occasion resource
    name: Mapped[str]

    #: a description of the occasion resource
    description: Mapped[str | None]

    #: the required range of resources
    number: Mapped[BoundedIntegerRange] = mapped_column(INT4RANGE)

    #: true if volunteers may sign up for this
    accept_signups: Mapped[bool] = mapped_column(default=False)

    #: The associated occasion
    occasion_id: Mapped[UUID] = mapped_column(ForeignKey('occasions.id'))
    occasion: Mapped[Occasion] = relationship(back_populates='needs')

    volunteers: Mapped[list[Volunteer]] = relationship(
        back_populates='need',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        UniqueConstraint(
            'name', 'occasion_id', name='unique_need_per_occasion'),
    )
