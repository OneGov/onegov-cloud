from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.models import ElectionCompound


class PartyPanachageResult(Base, TimestampMixin):

    __tablename__ = 'party_panachage_results'

    #: identifies the result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the election id this result belongs to
    election_id: Column[str | None] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: the election this result belongs to
    election: relationship[ProporzElection | None] = relationship(
        'ProporzElection',
        back_populates='party_panachage_results'
    )

    #: the election compound id this result belongs to
    election_compound_id: Column[str | None] = Column(
        Text,
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    #: the election compound this result belongs to
    election_compound: relationship[ElectionCompound | None] = relationship(
        'ElectionCompound',
        back_populates='party_panachage_results'
    )

    #: the party target this result belongs to, maps to party_id
    target: Column[str] = Column(Text, nullable=False)

    #: the party source this result belongs to, maps to party_id; might also
    #: refer to the black list by being empty
    source: Column[str] = Column(Text, nullable=False)

    # votes
    votes: Column[int] = Column(Integer, nullable=False, default=lambda: 0)
