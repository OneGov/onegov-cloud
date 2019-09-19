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
    validations = defaultdict(list)
    summary = OrderedDict()

    for lid, g in groupby(result, lambda l: l.id):
        for lst in g:
            # checks
            lst_ids.add(lst.id)
            lst_list_ids.add(lst.list_id)
            lst_names.add(lst.name)

            summary.setdefault('election_list_votes',
                               int(lst.election_list_votes))
            summary.setdefault('election_candidate_votes',
                               int(lst.election_candidate_votes))

            key = lst.name
            data.setdefault(
                key,
                {
                    'name': lst.name,
                    'list_id': lst.list_id,
                    'votes': lst.list_votes,
                    'total_candidate_votes': int(lst.candidate_votes_by_list),
                    'perc_to_total_votes': float(lst.perc_to_total_votes),
                    'number_of_mandates': lst.number_of_mandates
                    if election.completed else 0,
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

    total_list_votes = 0

    for name, item in data.items():
        if item['votes'] < item['total_candidate_votes']:
            validations['errors'].append(
                f'List {name} has more candidates votes than list votes.'
            )
        total_list_votes += item['votes']

    assert summary['election_list_votes'] == total_list_votes

    if summary['election_list_votes'] < summary['election_candidate_votes']:
        validations['errors'].append(
            f"The election has less list votes than candidate votes"
        )

    return {
        'summary': summary,
        'validations': validations,
        'results': data
    }


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
    # Fixme: Rewrite this function, it is very confusing what is does and why
    if election.type == 'majorz':
        return {}

    if not election.has_lists_panachage_data:
        return {}

    blank = request.translate(_("Blank list")) if request else '-'

    nodes = OrderedDict()
    nodes['left.999'] = {'name': blank}
    for list_ in election.lists.order_by(List.name):
        nodes[f'left.{list_.list_id}'] = {'name': list_.name}
    for list_ in election.lists:
        nodes[f'right.{list_.list_id}'] = {'name': list_.name}
    node_keys = list(nodes.keys())

    links = []
    for list_target in election.lists:
        target = node_keys.index(f'right.{list_target.list_id}')
        remaining = list_target.votes - sum(
            [r.votes for r in list_target.panachage_results]
        )
        for result in list_target.panachage_results:
            source = node_keys.index(f'left.{result.source}')
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
