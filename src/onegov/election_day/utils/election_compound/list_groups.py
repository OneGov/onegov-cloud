from onegov.ballot import PartyResult
from sqlalchemy import func
from sqlalchemy import Integer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from onegov.ballot.models import ElectionCompound
    from onegov.core.types import JSONObject_ro
    from sqlalchemy.orm import Query
    from typing import NamedTuple

    class ListGroupsRow(NamedTuple):
        name: str | None
        voters_count: Decimal | None
        number_of_mandates: int


def get_list_groups(
    election_compound: 'ElectionCompound'
) -> list['ListGroupsRow']:
    """" Get list groups data. """

    if not election_compound.pukelsheim:
        return []

    base_query = election_compound.party_results
    query: 'Query[ListGroupsRow]'
    if election_compound.exact_voters_counts:
        query = base_query.with_entities(
            PartyResult.name.label('name'),
            PartyResult.voters_count,
            PartyResult.number_of_mandates,
        )
    else:
        query = base_query.with_entities(
            PartyResult.name.label('name'),
            func.cast(
                func.round(PartyResult.voters_count),
                Integer
            ).label('voters_count'),
            PartyResult.number_of_mandates,
        )
    query = query.filter(
        PartyResult.year == election_compound.date.year,
        PartyResult.domain == election_compound.domain
    )
    query = query.order_by(
        PartyResult.voters_count.desc(),
        PartyResult.name,
    )

    return query.all()


def get_list_groups_data(
    election_compound: 'ElectionCompound'
) -> 'JSONObject_ro':
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
