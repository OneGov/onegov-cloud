
def get_list_results(election_compound, limit=None, names=None):
    """ Returns the aggregated list results as a list.

    Sorts them by mandates if the election is completed, else by voters count.

    Only if Doppelter Pukelsheim.

    """

    return election_compound.get_list_results(limit, names)


def get_lists_data(election_compound, limit=None, names=None):
    """" View the aggregated list results as JSON.

    Used to for the lists bar chart. Shows the mandates if the election
    is completed, the voters count if not.

    Only if Doppelter Pukelsheim.

    """

    completed = election_compound.completed
    colors = election_compound.colors
    default_color = '#999' if election_compound.colors else ''
    results = election_compound.get_list_results(limit, names)

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
                'color': colors.get(result.name) or default_color
            }
            for result in results
        ]
    }
