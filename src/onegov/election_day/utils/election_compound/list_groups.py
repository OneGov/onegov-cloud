from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from decimal import Decimal
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import PartyResult
    from onegov.core.types import JSONObject_ro


class ListGroupsRow(NamedTuple):
    name: str | None
    voters_count: Decimal | int | None
    number_of_mandates: int


def get_list_groups(
    election_compound: ElectionCompound
) -> list[ListGroupsRow]:
    """" Get list groups data. """

    if not election_compound.pukelsheim:
        return []

    def get_voters_count(result: PartyResult) -> Decimal | int | None:
        if result.voters_count is None:
            return result.voters_count
        if election_compound.exact_voters_counts:
            return result.voters_count
        return round(result.voters_count)

    results = [
        ListGroupsRow(
            name=result.name,
            voters_count=get_voters_count(result),
            number_of_mandates=result.number_of_mandates
        )
        for result in election_compound.party_results
        if (
            result.year == election_compound.date.year
            and result.domain == election_compound.domain
        )
    ]
    return sorted(results, key=lambda r: (-(r.voters_count or 0), r.name))


def get_list_groups_data(
    election_compound: ElectionCompound
) -> JSONObject_ro:
    """" Get the list groups bar chart data as JSON. """

    results = get_list_groups(election_compound)
    if not results:
        return {'results': []}

    allocated_mandates = election_compound.allocated_mandates
    return {
        'results': [
            {
                'text': result.name,
                'value': round(result.voters_count or 0),
                'value2': result.number_of_mandates,
                'class': (
                    'active'
                    if result.number_of_mandates or not allocated_mandates
                    else 'inactive'
                ),
                'color': election_compound.colors.get(result.name or '')
            } for result in results
        ],
    }
