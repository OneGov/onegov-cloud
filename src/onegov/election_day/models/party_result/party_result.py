from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Mapping
    from decimal import Decimal
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.models import ElectionCompound


class PartyResult(Base, TimestampMixin):
    """ The election result of a party in an election for a given year. """

    __tablename__ = 'party_results'

    #: identifies the party result
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
        back_populates='party_results'
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
        back_populates='party_results'
    )

    #: the domain of this result
    domain: Column[str | None] = Column(Text, nullable=True)

    #: the domain segment of this result
    domain_segment: Column[str | None] = Column(Text, nullable=True)

    #: the number of mandates
    number_of_mandates: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: the number of votes
    votes: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: the number of total votes
    total_votes: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: the number of total votes divided by the total number of mandates,
    #: used instead of total_votes by election compounds
    voters_count: Column[Decimal | None] = Column(
        Numeric(12, 2),
        nullable=True,
        default=lambda: 0
    )

    #: the voters count as percentage
    voters_count_percentage: Column[Decimal | None] = Column(
        Numeric(12, 2),
        nullable=True,
        default=lambda: 0
    )

    #: all translations of the party name
    name_translations: Column[Mapping[str, str]] = Column(
        HSTORE,
        nullable=False
    )

    #: the name of the party (uses the locale of the request, falls back to the
    #: default locale of the app)
    name = translation_hybrid(name_translations)

    #: the year
    year: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: the id of the party
    party_id: Column[str] = Column(Text, nullable=False)
