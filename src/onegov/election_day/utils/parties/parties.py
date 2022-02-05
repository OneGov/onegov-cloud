from onegov.ballot import PartyResult
from onegov.election_day import _
from sqlalchemy import func
from sqlalchemy.orm import object_session


def has_party_results(item):
    """ Returns True, if the item has party results. """

    if getattr(item, 'type', 'proporz') == 'proporz':
        if item.party_results.first():
            return True
    return False


def get_party_results(item):

    """ Returns the aggregated party results as list.

    Adds `voters_count` for election compounds with Doppelter Pukelsheim, else
    `votes`.

    """

    if not has_party_results(item):
        return [], {}

    session = object_session(item)
    pukelsheim = getattr(item, 'pukelsheim', False) == True

    # Get the totals votes per year
    if pukelsheim:
        query = session.query(
            PartyResult.year,
            func.sum(PartyResult.voters_count)
        )
        query = query.filter(PartyResult.owner == item.id)
        query = query.group_by(PartyResult.year)
    else:
        query = session.query(PartyResult.year, PartyResult.total_votes)
        query = query.filter(PartyResult.owner == item.id).distinct()
    totals = dict(query)
    years = sorted((str(key) for key in totals.keys()))

    parties = {}
    for result in item.party_results:
        party = parties.setdefault(result.name, {})
        year = party.setdefault(str(result.year), {})
        year['color'] = result.color
        year['mandates'] = result.number_of_mandates
        total = result.voters_count if pukelsheim else result.votes
        year['voters_count' if pukelsheim else 'votes'] = {
            'total': total,
            'permille': int(
                round(1000 * ((total or 0) / (totals.get(result.year) or 1)))
            )
        }

    return years, parties


def get_party_results_deltas(item, years, parties):

    """ Returns the aggregated party results with the differences to the
    last elections.

    """

    pukelsheim = getattr(item, 'pukelsheim', False) == True
    attribute = 'voters_count' if pukelsheim else 'votes'
    deltas = len(years) > 1
    results = {}
    for index, year in enumerate(years):
        results[year] = []
        for key in sorted(parties.keys()):
            result = [key]
            party = parties[key]
            values = party.get(year)
            if values:
                result.append(values.get('mandates', ''))
                result.append(values.get(attribute, {}).get('total', ''))
                permille = values.get(attribute, {}).get('permille')
                result.append(f'{permille/10}%' if permille else '')
            else:
                result.append('')
                result.append('')
                result.append('')

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

    pukelsheim = getattr(item, 'pukelsheim', False) == True
    attribute = 'voters_count' if pukelsheim else 'votes'
    years, parties = get_party_results(item)
    names = sorted(parties.keys())

    results = []
    for party in names:
        for year in parties[party]:
            front = parties[party].get(year, {}).get('mandates', 0)
            back = parties[party].get(year, {}).get(attribute, {})
            back = back.get('permille', 0) / 10.0
            color = parties[party].get(year, {}).get('color', '#999999')
            results.append({
                'group': party,
                'item': year,
                'value': {
                    'front': front,
                    'back': back,
                },
                'active': year == str(item.date.year),
                'color': color
            })

    return {
        'groups': names,
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
        | set([result.name for result in party_results])
    )

    def left_node(party):
        return parties.index(party)

    def right_node(party):
        return parties.index(party) + len(parties)

    colors = dict(set((r.name, r.color) for r in party_results))
    intra_party_votes = dict(set((r.name, r.votes) for r in party_results))

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
    blank = request.translate(_("Blank list")) if request else '-'
    nodes = [
        {
            'name': name or blank,
            'id': count + 1,
            'color': colors.get(name, '#999')
        }
        for count, name in enumerate(2 * parties)
    ]

    return {
        'nodes': nodes,
        'links': links,
        'title': item.title
    }
