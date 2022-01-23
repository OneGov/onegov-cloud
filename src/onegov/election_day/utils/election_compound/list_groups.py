from onegov.ballot import PartyResult


def get_list_groups(election_compound):
    """" Get list groups data. """

    if not election_compound.pukelsheim:
        return {}

    query = election_compound.party_results.filter(
        PartyResult.year == election_compound.date.year
    )
    if election_compound.completed:
        query = query.order_by(
            PartyResult.number_of_mandates.desc(),
            PartyResult.name,
        )
    else:
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
                'value': (
                    result.number_of_mandates if completed
                    else result.voters_count
                ),
                'value2': None,
                'class': (
                    'active' if completed and result.number_of_mandates
                    else 'inactive'
                ),
                'color': result.color
            } for result in results
        ],
    }
