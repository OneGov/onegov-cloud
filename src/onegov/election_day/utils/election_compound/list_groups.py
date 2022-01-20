from onegov.ballot import PartyResult


def get_list_groups(item):
    """" Get list groups data. """

    if getattr(item, 'type', 'proporz') == 'majorz':
        return {}

    results = item.party_results.filter(PartyResult.year == item.date.year)
    results = results.order_by(
        PartyResult.voters_count.desc(),
        PartyResult.number_of_mandates.desc(),
    )
    return results.all()


def get_list_groups_data(item):
    """" Get the list groups bar chart data as JSON. """

    results = get_list_groups(item)
    if not results:
        return {}

    return {
        'results': [
            {
                'text': result.name,
                'value': result.voters_count,
                'value2': result.number_of_mandates,
                'class': (
                    'active' if result.number_of_mandates and item.completed
                    else 'inactive'
                ),
                'color': result.color
            } for result in results
        ],
    }
