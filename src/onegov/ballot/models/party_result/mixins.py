from onegov.ballot.models.party_result.party_panachage_result import (
    PartyPanachageResult)
from onegov.ballot.models.party_result.party_result import PartyResult
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from sqlalchemy import or_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from onegov.core.types import AppenderQuery
    from sqlalchemy import Column
    from sqlalchemy.orm import relationship, Query

    rel = relationship


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
        party_results: rel[AppenderQuery[PartyResult]]
        party_panachage_results: rel[AppenderQuery[PartyPanachageResult]]

    @property
    def has_party_results(self) -> bool:
        return self.party_results.filter(
            or_(
                PartyResult.votes > 0,
                PartyResult.voters_count > 0,
                PartyResult.number_of_mandates > 0
            )
        ).first() is not None

    @property
    def has_party_panachage_results(self) -> bool:
        return self.party_panachage_results.filter(
            PartyPanachageResult.votes > 0
        ).first() is not None


class HistoricalPartyResultsMixin:

    if TYPE_CHECKING:
        # forward declare required relationships
        date: Column[datetime.date]
        party_results: relationship[AppenderQuery[PartyResult]]

    @property
    def relationships_for_historical_party_results(self) -> 'Query[Any]':
        raise NotImplementedError()

    @property
    def historical_party_results(self) -> 'Query[PartyResult]':
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
                related.target for related in relationships
                if related.target.date < self.date
            ),
            key=lambda related: related.date,
            reverse=True
        )
        if not target:
            return self.party_results

        return self.party_results.union(
            target[0].party_results.filter_by(year=target[0].date.year)
        )

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
