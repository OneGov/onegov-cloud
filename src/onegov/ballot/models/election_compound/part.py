from onegov.ballot.models.election_compound.mixins import (
    DerivedAttributesMixin)
from onegov.ballot.models.party_result.mixins import (
    HistoricalPartyResultsMixin)
from onegov.ballot.models.party_result.mixins import PartyResultsCheckMixin


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from onegov.ballot.models.election import Election
    from onegov.ballot.models.election_compound.election_compound import (
        ElectionCompound)
    from onegov.ballot.models.election_compound.relationship import (
        ElectionCompoundRelationship)
    from onegov.ballot.models.party_result import PartyResult
    from onegov.ballot.types import DomainOfInfluence  # noqa: F401
    from onegov.core.orm import SessionManager  # noqa: F401
    from sqlalchemy.orm import Query


T = TypeVar('T')


class inherited_attribute(Generic[T]):

    def __set_name__(
        self,
        owner: type[Any],
        name: str
    ) -> None:

        self.name = name

    def __get__(
        self,
        # NOTE: Because we mix ElectionCompoundPart with other objects mypy
        #       will complain about inherited_attribute not working on these
        #       other objects, since information is lost during type union
        #       so for now we ignore type safety here, it should be fine
        instance: Any,
        owner: type[Any]
    ) -> T:

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

    # NOTE: These top three attributes are a bit ugly due to the mixins
    #       forward declaring these attributes as columns, even though they
    #       can be arbitrary readable attributes, which cannot be expressed
    #       yet using a Protocol, once we can do that, this should become
    #       cleaner
    date: inherited_attribute['datetime.date'] = (
        inherited_attribute['datetime.date']())  # type:ignore[assignment]
    completes_manually: inherited_attribute[bool] = (
        inherited_attribute[bool]())  # type:ignore[assignment]
    manually_completed: inherited_attribute[bool] = (
        inherited_attribute[bool]())  # type:ignore[assignment]
    pukelsheim = inherited_attribute[bool]()
    last_result_change = inherited_attribute['datetime.datetime | None']()
    last_change = inherited_attribute['datetime.datetime | None']()
    last_modified = inherited_attribute['datetime.datetime | None']()
    domain_elections = inherited_attribute['DomainOfInfluence']()
    colors = inherited_attribute[dict[str, str]]()
    voters_counts = inherited_attribute[bool]()
    exact_voters_counts = inherited_attribute[bool]()
    horizontal_party_strengths = inherited_attribute[bool]()
    show_party_strengths = inherited_attribute[bool]()
    use_historical_party_results = inherited_attribute[bool]()
    session_manager = inherited_attribute['SessionManager']()

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
    def progress(self) -> tuple[int, int]:
        result = [e.completed for e in self.elections]
        return sum(1 for r in result if r), len(result)

    @property
    def party_results(self) -> 'list[PartyResult]':  # type:ignore[override]
        return [
            result for result in self.election_compound.party_results
            if (
                result.domain == self.domain
                and result.domain_segment == self.segment
            )
        ]

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
