
def get_list_results(election_compound, limit=None, names=None):
    """ Returns the aggregated list results as list. """

    if election_compound.pukelsheim:
        return election_compound.get_list_results(
            order_by='number_of_mandates'
        )
    return election_compound.get_list_results()


def get_lists_data(election_compound, limit=None, names=None,
                   mandates_only=False):
    """" View the lists as JSON. Used to for the lists bar chart. """

    completed = election_compound.completed
    colors = election_compound.colors
    default_color = '#999' if election_compound.colors else ''

    if not mandates_only:
        return {
            'results': [
                {
                    'text': list_.name,
                    'value': list_.votes,
                    'value2': list_.number_of_mandates,
                    'class': 'active' if completed else 'inactive',
                    'color': colors.get(list_.name) or default_color
                }
                for list_ in election_compound.get_list_results(
                    limit=limit, names=names
                )
            ]
        }

    else:
        return {
            'results': [
                {
                    'text': list_.name,
                    'value': list_.number_of_mandates,
                    'value2': None,
                    'class': 'active' if completed else 'inactive',
                    'color': colors.get(list_.name) or default_color
                }
                for list_ in election_compound.get_list_results(
                    limit=limit,
                    names=names,
                    order_by='number_of_mandates'
                )
            ]
        }
