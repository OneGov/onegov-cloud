from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.models import ElectionCompound


class PartyResult(Base, TimestampMixin):
    """ The election result of a party in an election for a given year. """

    __tablename__ = 'party_results'

    #: identifies the party result
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the election id this result belongs to
    election_id: Mapped[str | None] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    #: the election this result belongs to
    election: Mapped[ProporzElection | None] = relationship(
        back_populates='party_results'
    )

    #: the election compound id this result belongs to
    election_compound_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        )
    )

    #: the election compound this result belongs to
    election_compound: Mapped[ElectionCompound | None] = relationship(
        back_populates='party_results'
    )

    #: the domain of this result
    domain: Mapped[str | None]

    #: the domain segment of this result
    domain_segment: Mapped[str | None]

    #: the number of mandates
    number_of_mandates: Mapped[int] = mapped_column(default=lambda: 0)

    #: the number of votes
    votes: Mapped[int] = mapped_column(default=lambda: 0)

    #: the number of total votes
    total_votes: Mapped[int] = mapped_column(default=lambda: 0)

    #: the number of total votes divided by the total number of mandates,
    #: used instead of total_votes by election compounds
    voters_count: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        default=lambda: 0
    )

    #: the voters count as percentage
    voters_count_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        default=lambda: 0
    )

    #: all translations of the party name
    name_translations: Mapped[Mapping[str, str]] = mapped_column(HSTORE)

    #: the name of the party (uses the locale of the request, falls back to the
    #: default locale of the app)
    name = translation_hybrid(name_translations)

    #: the year
    year: Mapped[int] = mapped_column(default=lambda: 0)

    #: the id of the party
    party_id: Mapped[str]
