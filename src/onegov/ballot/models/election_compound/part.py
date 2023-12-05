from onegov.ballot.models.election_compound.mixins import (
    DerivedAttributesMixin)
from onegov.ballot.models.party_result.mixins import (
    HistoricalPartyResultsMixin)
from onegov.ballot.models.party_result.mixins import PartyResultsCheckMixin
from sqlalchemy.orm import object_session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from onegov.ballot.types import DomainOfInfluence
    from onegov.core.orm import SessionManager
    from sqlalchemy.orm import Query, Session

    from .election_compound import ElectionCompound
    from .relationship import ElectionCompoundRelationship
    from ..election import Election
    from ..party_result import PartyResult


if TYPE_CHECKING:
    # HACK: this is the only way that allows us to specify what type
    #       these attributes should actually have
    def inherited_attribute() -> Any: ...


class inherited_attribute:  # type:ignore[no-redef]  # noqa: F811

    def __set_name__(
        self,
        owner: type['ElectionCompoundPart'],
        name: str
    ) -> None:

        self.name = name

    def __get__(
        self,
        instance: 'ElectionCompoundPart',
        owner: type['ElectionCompoundPart']
    ) -> Any:

        return getattr(instance.election_compound, self.name)


class ElectionCompoundPart(
    DerivedAttributesMixin, PartyResultsCheckMixin, HistoricalPartyResultsMixin
):

    """ A part of an election compound.

    Covers a part of an election compound between the domain of the compound
    and the domain of the elections.

    There is no database object behind a part of an election compound, all
    the results are either taken from the compound (parties) or elections
    (candidates)-

    """

    def __init__(
        self,
        election_compound: 'ElectionCompound',
        domain: str,
        segment: str
    ):
        self.election_compound = election_compound
        self.election_compound_id = (
            election_compound.id if election_compound else None
        )
        self.domain = domain
        self.segment = segment
        self.id = segment.replace(' ', '-').lower()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ElectionCompoundPart)
            and self.election_compound_id == other.election_compound_id
            and self.domain == other.domain
            and self.segment == other.segment
        )

    date: 'datetime.date' = inherited_attribute()  # type:ignore[assignment]
    completes_manually: bool = inherited_attribute()  # type:ignore[assignment]
    manually_completed: bool = inherited_attribute()  # type:ignore[assignment]
    pukelsheim: bool = inherited_attribute()
    last_result_change: 'datetime.datetime | None' = inherited_attribute()
    last_change: 'datetime.datetime | None' = inherited_attribute()
    last_modified: 'datetime.datetime | None' = inherited_attribute()
    domain_elections: 'DomainOfInfluence' = inherited_attribute()
    colors: dict[str, str] = inherited_attribute()
    voters_counts: bool = inherited_attribute()
    exact_voters_counts: bool = inherited_attribute()
    horizontal_party_strengths: bool = inherited_attribute()
    show_party_strengths: bool = inherited_attribute()
    use_historical_party_results: bool = inherited_attribute()
    session_manager: 'SessionManager' = inherited_attribute()

    @property
    def title(self) -> str:
        return f'{self.election_compound.title} {self.segment}'

    @property
    def title_translations(self) -> dict[str, str]:
        return {
            locale: f'{title} {self.segment}'
            for locale, title
            in self.election_compound.title_translations.items()
        }

    @property
    def elections(self) -> list['Election']:
        return [
            election for election in
            self.election_compound.elections
            if election.domain_supersegment == self.segment
        ]

    @property
    def session(self) -> 'Session':
        return object_session(self.election_compound)

    @property
    def progress(self) -> tuple[int, int]:
        result = [e.completed for e in self.elections]
        return sum(1 for r in result if r), len(result)

    @property
    def party_results(self) -> 'Query[PartyResult]':  # type:ignore[override]
        return self.election_compound.party_results.filter_by(
            domain=self.domain, domain_segment=self.segment
        )

    @property
    def has_results(self) -> bool:
        """ Returns True, if the election compound has any results. """

        if self.has_party_results:
            return True
        for election in self.elections:
            if election.has_results:
                return True

        return False

    @property
    def relationships_for_historical_party_results(
        self
    ) -> 'Query[ElectionCompoundRelationship]':
        return self.election_compound.related_compounds
