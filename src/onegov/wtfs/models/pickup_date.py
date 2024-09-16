from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.wtfs.models.municipality import Municipality
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t


class PickupDate(Base, TimestampMixin):
    """ A pick-up date. """

    __tablename__ = 'wtfs_pickup_dates'

    #: the id of the db record (only relevant internally)
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the date
    date: 'Column[date_t]' = Column(Date, nullable=False)

    #: the id of the municipality
    municipality_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(Municipality.id),
        nullable=False
    )

    #: the municipality
    municipality: 'relationship[Municipality]' = relationship(
        Municipality,
        back_populates='pickup_dates'
    )
