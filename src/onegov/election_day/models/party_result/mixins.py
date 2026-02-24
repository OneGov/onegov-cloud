from __future__ import annotations

from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import PartyPanachageResult
    from onegov.election_day.models import PartyResult
    from sqlalchemy.orm import Mapped
    from sqlalchemy.orm import Query
    import datetime


class PartyResultsOptionsMixin:

    #: Display voters counts instead of votes in views.
    voters_counts: dict_property[bool] = meta_property(default=False)

    #: Display exact voters counts instead of rounded values.
    exact_voters_counts: dict_property[bool] = meta_property(default=False)

    #: may be used to enable/disable the visibility of party strengths
    show_party_strengths: dict_property[bool] = meta_property(default=False)

    #: show a horizontal party strengths bar chart instead of a vertical
    horizontal_party_strengths: dict_property[bool] = meta_property(
        default=False
    )

    #: may be used to enable/disable the visibility of party panachage
    show_party_panachage: dict_property[bool] = meta_property(default=False)

    #: may be used to enable/disable the visibility of the seat allocation
    show_seat_allocation: dict_property[bool] = meta_property(default=False)

    #: may be used to enable/disable the visibility of the list groups
    show_list_groups: dict_property[bool] = meta_property(default=False)

    #: may be used to enable fetching party results from previous elections
    use_historical_party_results: dict_property[bool] = meta_property(
        default=False
    )


class PartyResultsCheckMixin:

    if TYPE_CHECKING:
        # forward declare required relationships
        party_results: Mapped[list[PartyResult]]
        party_panachage_results: Mapped[list[PartyPanachageResult]]

    @property
    def has_party_results(self) -> bool:
        for result in self.party_results:
            if (
                result.votes
                or result.voters_count
                or result.number_of_mandates
            ):
                return True
        return False

    @property
    def has_party_panachage_results(self) -> bool:
        for result in self.party_panachage_results:
            if result.votes:
                return True
        return False


class HistoricalPartyResultsMixin:

    if TYPE_CHECKING:
        # forward declare required relationships
        date: Mapped[datetime.date]
        party_results: Mapped[list[PartyResult]]

    @property
    def relationships_for_historical_party_results(self) -> Query[Any]:
        raise NotImplementedError()

    @property
    def historical_party_results(self) -> list[PartyResult]:
        """ Returns the party results while adding party results from the last
        legislative period, Requires that a related election or compound has
        been set with type "historical".

        """

        query = self.relationships_for_historical_party_results
        relationships = query.filter_by(type='historical').all()
        if not relationships:
            return self.party_results
        target = sorted(
            (
                relationship.target for relationship in relationships
                if relationship.target.date < self.date
            ),
            key=lambda related: related.date,
            reverse=True
        )
        if not target:
            return self.party_results

        return self.party_results + [
            result for result in target[0].party_results
            if result.year == target[0].date.year
        ]

    @property
    def historical_colors(self) -> dict[str, str]:
        result = getattr(self, 'colors', {}).copy()
        if not result:
            return result
        relationships = self.relationships_for_historical_party_results
        relationships = relationships.filter_by(type='historical')
        for relation in relationships:
            for key, value in getattr(relation.target, 'colors', {}).items():
                result.setdefault(key, value)
        return result
