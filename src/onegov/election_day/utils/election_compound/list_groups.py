from onegov.ballot import PartyResult


def get_list_groups(election_compound):
    """" Get list groups data. """

    if getattr(election_compound, 'type', 'proporz') == 'majorz':
        return {}

    results = election_compound.party_results.filter(
        PartyResult.year == election_compound.date.year
    )
    results = results.order_by(
        PartyResult.voters_count.desc(),
        PartyResult.number_of_mandates.desc(),
    )
    return results.all()


def get_list_groups_data(election_compound):
    """" Get the list groups bar chart data as JSON. """

    results = get_list_groups(election_compound)
    if not results:
        return {}

    return {
        'results': [
            {
                'text': result.name,
                'value': result.voters_count,
                'value2': result.number_of_mandates,
                'class': (
                    'active' if (
                        result.number_of_mandates
                        and election_compound.completed
                    ) else 'inactive'
                ),
                'color': result.color
            } for result in results
        ],
    }
