from __future__ import annotations

from onegov.core.orm import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Election


class ElectionRelationship(Base):
    """ A relationship between elections. """

    __tablename__ = 'election_relationships'

    #: Identifies the relationship.
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The source election ID.
    source_id: Mapped[str] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE')
    )

    #: The target election ID.
    target_id: Mapped[str] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The source election.
    source: Mapped[Election] = relationship(
        foreign_keys=[source_id],
        back_populates='related_elections'
    )

    #: The target election.
    target: Mapped[Election] = relationship(
        foreign_keys=[target_id],
        back_populates='referencing_elections'
    )

    #: the type of relationship
    type: Mapped[str | None]
