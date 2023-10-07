from collections import OrderedDict
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListResult
from onegov.election_day import _
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import object_session
from sqlalchemy.sql.expression import case


def get_list_results(election, limit=None, names=None, sort_by_names=None,
                     entities=None):
    """ Returns the aggregated list results as list. """

    session = object_session(election)
    result = session.query(
        func.sum(ListResult.votes).label('votes'),
        List.name,
        List.number_of_mandates
    )
    result = result.join(ListResult.list)
    result = result.filter(List.election_id == election.id)
    if names:
        result = result.filter(List.name.in_(names))
    if entities:
        election_result_id = session.query(ElectionResult.id).filter(
            ElectionResult.election_id == election.id,
            ElectionResult.name.in_(entities)
        )
        election_result_id = [result.id for result in election_result_id]
        result = result.filter(
            ListResult.election_result_id.in_(election_result_id)
        )
    result = result.group_by(
        List.name,
        List.number_of_mandates
    )
    order = [desc('votes')]
    if names and sort_by_names:
        order.insert(0, case(
            [
                (List.name == name, index)
                for index, name in enumerate(names, 1)
            ],
            else_=0
        ))
    result = result.order_by(*order)

    if limit and limit > 0:
        result = result.limit(limit)

    return result


def get_lists_data(
    election, limit=None, names=None, mandates_only=False, sort_by_names=None,
    entities=None
):
    """" View the lists as JSON. Used to for the lists bar chart. """

    allocated_mandates = election.allocated_mandates
    colors = election.colors

    if election.type == 'majorz':
        return {
            'results': [],
            'majority': None,
            'title': election.title
        }

    return {
        'results': [
            {
                'text': list_.name,
                'value': list_.votes,
                'value2': list_.number_of_mandates,
                'class': (
                    'active'
                    if list_.number_of_mandates or not allocated_mandates
                    else 'inactive'
                ),
                'color': colors.get(list_.name)
            }
            for list_ in get_list_results(
                election, limit=limit, names=names,
                sort_by_names=sort_by_names, entities=entities
            )
        ],
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
        nodes[f'left.{list_.list_id}'] = {
            'name': list_.name,
            'color': election.colors.get(list_.name),
            'active': list_.number_of_mandates > 0
        }
    for list_ in election.lists:
        nodes[f'right.{list_.list_id}'] = {
            'name': list_.name,
            'color': election.colors.get(list_.name),
            'active': list_.number_of_mandates > 0
        }
    node_keys = list(nodes.keys())

    links = []
    list_ids = {list.id: list.list_id for list in election.lists}
    list_ids[None] = '999'
    for list_target in election.lists:
        target_index = node_keys.index(f'right.{list_target.list_id}')
        for result in list_target.panachage_results:
            source_list_id = list_ids[result.source_id]
            source_key = f'left.{source_list_id}'
            source_item = nodes.get(source_key, {})
            source_index = node_keys.index(source_key)
            votes = result.votes
            if list_target.list_id == source_list_id:
                continue
            links.append({
                'source': source_index,
                'target': target_index,
                'value': votes,
                'color': source_item.get('color'),
                'active': source_item.get('active')
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
