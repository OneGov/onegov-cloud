from collections import OrderedDict
from onegov.ballot import List
from onegov.election_day import _
from sqlalchemy import desc
from sqlalchemy.orm import object_session


def get_list_results(election, session):
    """ Returns the aggregated list results as list. """

    result = session.query(
        List.name, List.votes, List.list_id, List.number_of_mandates
    )
    result = result.order_by(desc(List.votes))
    result = result.filter(List.election_id == election.id)

    return result


def get_lists_data(election, request):
    """" View the lists as JSON. Used to for the lists bar chart. """

    if election.type == 'majorz':
        return {
            'results': [],
            'majority': None,
            'title': election.title
        }

    return {
        'results': [{
            'text': item[0],
            'value': item[1],
            'value2': item[3],
            'class': 'active' if item[3] else 'inactive',
        } for item in get_list_results(election, object_session(election))],
        'majority': None,
        'title': election.title
    }


def get_lists_panachage_data(election, request):
    """" Get the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    if election.type == 'majorz':
        return {}

    if not election.has_lists_panachage_data:
        return {}

    blank = request.translate(_("Blank list")) if request else '-'

    nodes = OrderedDict()
    nodes['left.999'] = {'name': blank}
    for list_ in election.lists.order_by(List.name):
        nodes['left.{}'.format(list_.list_id)] = {'name': list_.name}
    for list_ in election.lists:
        nodes['right.{}'.format(list_.list_id)] = {'name': list_.name}
    node_keys = list(nodes.keys())

    links = []
    for list_target in election.lists:
        target = node_keys.index('right.{}'.format(list_target.list_id))
        remaining = list_target.votes - sum(
            [r.votes for r in list_target.panachage_results]
        )
        for result in list_target.panachage_results:
            source = node_keys.index('left.{}'.format(result.source))
            votes = result.votes
            if list_target.list_id == result.source:
                votes += remaining
            links.append({
                'source': source,
                'target': target,
                'value': votes
            })

    count = 0
    for key in nodes.keys():
        count = count + 1
        nodes[key]['id'] = count

    return {
        'nodes': list(nodes.values()),
        'links': links,
        'title': election.title
    }
