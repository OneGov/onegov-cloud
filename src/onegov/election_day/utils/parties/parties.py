from decimal import Decimal
from onegov.ballot import PartyResult
from onegov.election_day import _
from sqlalchemy.orm import object_session


def has_party_results(item):
    """ Returns True, if the item has party results. """

    if getattr(item, 'type', 'proporz') == 'proporz':
        if item.party_results.first():
            return True
    return False


def get_party_results(item, json_serializable=False):

    """ Returns the aggregated party results as list.

    Adds `voters_count` for election compounds with voters counts enabled, else
    `votes`.

    """

    if not has_party_results(item):
        return [], {}

    session = object_session(item)

    exact = getattr(item, 'exact_voters_counts', False) is True

    # Get the totals votes per year
    query = session.query(PartyResult.year, PartyResult.total_votes)
    query = query.filter(PartyResult.owner == item.id).distinct()
    totals_votes = dict(query)
    years = sorted((str(key) for key in totals_votes.keys()))

    parties = {}
    for result in item.party_results:
        party = parties.setdefault(result.party_id, {})
        year = party.setdefault(str(result.year), {})
        year['color'] = result.color
        year['mandates'] = result.number_of_mandates
        year['name'] = result.name

        votes = result.votes or 0
        total_votes = totals_votes.get(result.year) or 0
        votes_permille = 0
        if total_votes:
            votes_permille = int(round(1000 * (votes / total_votes)))
        year['votes'] = {
            'total': votes,
            'permille': votes_permille
        }

        voters_count = result.voters_count or Decimal(0)
        if not exact:
            voters_count = int(round(voters_count))
        elif json_serializable:
            voters_count = float(voters_count)
        voters_count_permille = result.voters_count_percentage or Decimal(0)
        voters_count_permille = 10 * voters_count_permille
        if json_serializable:
            voters_count_permille = float(voters_count_permille)
        year['voters_count'] = {
            'total': voters_count,
            'permille': voters_count_permille
        }

    return years, parties


def get_party_results_deltas(item, years, parties):

    """ Returns the aggregated party results with the differences to the
    last elections.

    """

    voters_counts = getattr(item, 'voters_counts', False) == True
    attribute = 'voters_count' if voters_counts else 'votes'
    deltas = len(years) > 1
    results = {}
    for index, year in enumerate(years):
        results[year] = []
        for key in sorted(parties.keys()):
            result = ['', '', '', '']
            party = parties[key]
            values = party.get(year)
            if values:
                permille = values.get(attribute, {}).get('permille')
                result = [
                    values.get('name', ''),
                    values.get('mandates', ''),
                    values.get(attribute, {}).get('total', ''),
                    f'{permille/10}%' if permille else ''
                ]

            if deltas:
                delta = ''
                if index:
                    last = party.get(years[index - 1])
                    if values and last:
                        diff = (
                            (values.get(attribute, {}).get('permille', 0) or 0)
                            - (last.get(attribute, {}).get('permille', 0) or 0)
                        ) / 10
                        delta = '{}%'.format(diff)
                result.append(delta)

            results[year].append(result)

    return deltas, results


def get_party_results_data(item):

    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    if not has_party_results(item):
        return {
            'results': [],
            'title': item.title
        }

    voters_counts = getattr(item, 'voters_counts', False) == True
    attribute = 'voters_count' if voters_counts else 'votes'
    years, parties = get_party_results(item)
    groups = {}
    results = []
    for party_id in parties:
        for year in sorted(parties[party_id], reverse=True):
            group = groups.setdefault(
                party_id, parties[party_id].get(year, {}).get('name', party_id)
            )
            front = parties[party_id].get(year, {}).get('mandates', 0)
            back = parties[party_id].get(year, {}).get(attribute, {})
            back = float(back.get('permille', 0) / 10)
            color = parties[party_id].get(year, {}).get('color', '#999999')
            results.append({
                'group': group,
                'item': year,
                'value': {
                    'front': front,
                    'back': back,
                },
                'active': year == str(item.date.year),
                'color': color
            })

    return {
        'groups': [items[1] for items in sorted(list(groups.items()))],
        'labels': years,
        'maximum': {
            'front': item.number_of_mandates,
            'back': 100,
        },
        'axis_units': {
            'front': '',
            'back': '%'
        },
        'results': results,
        'title': item.title
    }


def get_parties_panachage_data(item, request=None):
    """" Get the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    if getattr(item, 'type', 'proporz') == 'majorz':
        return {}

    results = item.panachage_results.all()
    party_results = item.party_results.filter_by(year=item.date.year).all()
    if not results:
        return {}

    parties = sorted(
        set([result.source for result in results])
        | set([result.target for result in results])
        | set([result.party_id for result in party_results])
    )

    def left_node(party):
        return parties.index(party)

    def right_node(party):
        return parties.index(party) + len(parties)

    colors = dict(set((r.party_id, r.color) for r in party_results))
    intra_party_votes = dict(set((r.party_id, r.votes) for r in party_results))

    # Create the links
    links = []
    for result in results:
        if result.source == result.target:
            continue
        if result.target in intra_party_votes:
            intra_party_votes[result.target] -= result.votes
        links.append({
            'source': left_node(result.source),
            'target': right_node(result.target),
            'value': result.votes,
            'color': colors.get(result.source, '#999')
        })
    for party, votes in intra_party_votes.items():
        links.append({
            'source': left_node(party),
            'target': right_node(party),
            'value': votes,
            'color': colors.get(party, '#999')
        })

    # Create the nodes
    names = {r.party_id: r.name for r in party_results}
    blank = request.translate(_("Blank list")) if request else '-'
    nodes = [
        {
            'name': names.get(party_id, '') or blank,
            'id': count + 1,
            'color': colors.get(party_id, '#999')
        }
        for count, party_id in enumerate(2 * parties)
    ]

    return {
        'nodes': nodes,
        'links': links,
        'title': item.title
    }
