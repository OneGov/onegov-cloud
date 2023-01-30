from decimal import Decimal
from onegov.ballot import PartyResult
from onegov.election_day import _


def get_party_results(item, json_serializable=False):

    """ Returns the aggregated party results as list. """

    if not getattr(item, 'has_party_results', False):
        return [], {}

    party_results = (
        item.historical_party_results if item.use_historical_party_results
        else item.party_results
    )
    results = party_results.filter(PartyResult.domain == item.domain)
    domain_segment = getattr(item, 'segment', None)
    if domain_segment:
        results = results.filter(PartyResult.domain_segment == domain_segment)

    # Get the totals votes per year
    totals_votes = {r.year: r.total_votes for r in results}
    years = sorted((str(key) for key in totals_votes.keys()))

    # Get the results
    parties = {}
    for result in results:
        party = parties.setdefault(result.party_id, {})
        year = party.setdefault(str(result.year), {})
        year['color'] = item.colors.get(result.name)
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
        if not item.exact_voters_counts:
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

    attribute = 'voters_count' if item.voters_counts else 'votes'
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


def get_party_results_data(item, horizontal):
    """ Retuns the data used for the diagrams showing the party results. """
    if horizontal:
        return get_party_results_horizontal_data(item)
    return get_party_results_vertical_data(item)


def get_party_results_horizontal_data(item):

    """ Retuns the data used for the horitzonal bar diagram showing the party
    results.

    """

    if not getattr(item, 'has_party_results', False):
        return {
            'results': [],
        }

    attribute = 'voters_count' if item.voters_counts else 'votes'
    years, parties = get_party_results(item)
    allocated_mandates = item.allocated_mandates

    party_names = {}
    for party_id, party in parties.items():
        party_names[party_id] = None
        for year in party.values():
            party_names[party_id] = party_names[party_id] or year.get('name')

    results = []
    if years:
        year = years[-1]
        party_ids = [
            (values.get(year, {}).get(attribute, {}).get('total', 0), party_id)
            for party_id, values in parties.items()
        ]
        party_ids = [item[1] for item in sorted(party_ids)]
        for party_id in reversed(party_ids):
            for year in reversed(years):
                active = year == years[-1]
                party = parties.get(party_id, {}).get(year, {})
                name = party_names.get(party_id)
                if len(years) == 1:
                    text = name
                    value = round(
                        party.get(attribute, {}).get('total', 0) or 0
                    )
                    percentage = False
                else:
                    text = f'{name} {year}' if active else year
                    value = float(
                        (party.get(attribute, {}).get('permille', 0) or 0) / 10
                    )
                    percentage = True
                results.append({
                    'text': text,
                    'value': value,
                    'value2': party.get('mandates'),
                    'class': (
                        'active' if active and (
                            party.get('mandates') or not allocated_mandates
                        )
                        else 'inactive'
                    ),
                    'color': party.get('color'),
                    'percentage': percentage
                })

    return {'results': results}


def get_party_results_vertical_data(item):

    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    if not getattr(item, 'has_party_results', False):
        return {
            'results': [],
            'title': item.title
        }

    attribute = 'voters_count' if item.voters_counts else 'votes'
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


def get_party_results_seat_allocation(years, parties):

    """ Returns the aggregated party results for the seat allocation table.

    """
    if not years:
        return []

    party_names = {}
    for party_id, party in parties.items():
        party_names[party_id] = None
        for year in party.values():
            party_names[party_id] = party_names[party_id] or year.get('name')

    result = []
    for party_id, party in parties.items():
        row = []
        row.append(party_names.get(party_id, ''))
        for year in years:
            row.append(
                parties.get(party_id, {}).get(year, {}).get('mandates', 0)
            )
        result.append(row)

    return result


def get_parties_panachage_data(item, request=None):
    """" Get the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    if not getattr(item, 'has_party_panachage_results', False):
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

    active = {r.party_id: r.number_of_mandates > 0 for r in party_results}
    colors = {
        r.party_id: item.colors[r.name]
        for r in party_results
        if r.name in item.colors
    }
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
            'color': colors.get(result.source),
            'active': active.get(result.source, False)
        })
    for party, votes in intra_party_votes.items():
        links.append({
            'source': left_node(party),
            'target': right_node(party),
            'value': votes,
            'color': colors.get(party),
            'active': active.get(party, False)
        })

    # Create the nodes
    names = {r.party_id: r.name for r in party_results}
    blank = request.translate(_("Blank list")) if request else '-'
    nodes = [
        {
            'name': names.get(party_id, '') or blank,
            'id': count + 1,
            'color': colors.get(party_id),
            'active': active.get(party_id, False)
        }
        for count, party_id in enumerate(2 * parties)
    ]

    return {
        'nodes': nodes,
        'links': links,
        'title': item.title
    }
