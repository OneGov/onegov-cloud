from onegov.ballot import PartyResult
from sqlalchemy import func
from sqlalchemy import Integer


def get_list_groups(election_compound, domain=None, domain_segment=None):
    """" Get list groups data. """

    if not election_compound.pukelsheim:
        return {}

    query = election_compound.party_results
    if election_compound.exact_voters_counts:
        query = query.with_entities(
            PartyResult.name.label('name'),
            PartyResult.voters_count,
            PartyResult.number_of_mandates,
        )
    else:
        query = query.with_entities(
            PartyResult.name.label('name'),
            func.cast(
                func.round(PartyResult.voters_count),
                Integer
            ).label('voters_count'),
            PartyResult.number_of_mandates,
        )
    query = query.filter(
        PartyResult.year == election_compound.date.year,
        PartyResult.domain == (domain or election_compound.domain)
    )
    if domain_segment:
        query = query.filter(PartyResult.domain_segment == domain_segment)
    query = query.order_by(
        PartyResult.voters_count.desc(),
        PartyResult.name,
    )

    return query.all()


def get_list_groups_data(election_compound):
    """" Get the list groups bar chart data as JSON. """

    results = get_list_groups(election_compound)
    if not results:
        return {'results': []}

    completed = election_compound.completed
    return {
        'results': [
            {
                'text': result.name,
                'value': round(result.voters_count or 0),
                'value2': result.number_of_mandates,
                'class': (
                    'active' if completed and result.number_of_mandates
                    else 'inactive'
                ),
                'color': election_compound.colors.get(result.name)
            } for result in results
        ],
    }
