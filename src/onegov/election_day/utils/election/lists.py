from collections import OrderedDict, defaultdict
from itertools import groupby

from onegov.ballot import List
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.election_day import _
from sqlalchemy import desc, select
from sqlalchemy.orm import object_session


class LastUpdatedOrderedDict(OrderedDict):
    """
    Stores items in the order the keys were last added.
    """

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().move_to_end(key)


def get_aggregated_list_results(election, session, use_checks=False):
    if election.type == 'majorz':
        return {}

    agg_lr_query = as_selectable_from_path(
        module_path(
            'onegov.election_day', 'queries/aggregated_list_results.sql'))

    agg_lr = agg_lr_query.c
    query = select(agg_lr).where(agg_lr.election_id == election.id)
    result = session.execute(query)

    data = LastUpdatedOrderedDict({})

    # checks
    lst_ids = set()
    lst_list_ids = set()
    lst_names = set()

    for lid, g in groupby(result, lambda l: l.id):
        for lst in g:
            lst_ids.add(lst.id)
            lst_list_ids.add(lst.list_id)
            lst_names.add(lst.name)

            # key can be id or name, count was the same
            # key = f'{lst.name}-{lst.list_id}'
            key = lst.id
            data.setdefault(
                key,
                {
                    'name': lst.name,
                    'list_id': lst.list_id,
                    'number_of_mandates': lst.number_of_mandates,
                    'votes': lst.votes,
                    'perc_to_total_votes': float(lst.perc_to_total_votes),
                    'candidates': [],
                }
            )
            data[key]['candidates'].append({
                'family_name': lst.family_name,
                'first_name': lst.first_name,
                'total_votes': lst.candidate_votes,
                'perc_to_list_votes': float(lst.perc_to_list_votes)
            })

    # all of these must be unique for an election
    assert len(lst_ids) == len(lst_list_ids)
    assert len(lst_list_ids) == len(lst_names)

    check_msg = defaultdict(list)
    total_percentage = 0
    candidates_perc = defaultdict(int)
    candidates_votes = defaultdict(int)

    for name, item in data.items():
        total_percentage += item['perc_to_total_votes']
        for candidate in item['candidates']:
            candidates_perc[item['name']] += candidate['perc_to_list_votes']
            candidates_votes[item['name']] += candidate['total_votes']

    for name, perc in candidates_perc.items():
        if not perc <= 100:
            check_msg['total_percentages'].append({
                'name': name,
                'total_of_perc_to_list_votes': perc})

    if not total_percentage == 100:
        check_msg['total_percentages'].append({
            'total_of_perc_to_total_votes': total_percentage
        })

    return {'validations': check_msg, 'results': list(data.values())}


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
            'value2': item[3] if election.completed else None,
            'class': 'active' if election.completed
            and item[3] else 'inactive',
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
