from morepath.request import Response
from onegov.ballot import Election
from onegov.ballot import PartyResult
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout, ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy.orm import object_session


def has_party_results(item):
    """ Returns True, if the item has party results. """

    if getattr(item, 'type', 'proporz') == 'proporz':
        if item.party_results.first():
            return True
    return False


def get_party_results(item):

    """ Returns the aggregated party results as list. """

    if not has_party_results(item):
        return [], {}

    session = object_session(item)

    # Get the totals votes per year
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
        year['votes'] = {
            'total': result.votes,
            'permille': int(
                round(1000 * (result.votes / (totals.get(result.year) or 1)))
            )
        }

    return years, parties


def get_party_results_deltas(election, years, parties):

    """ Returns the aggregated party results with the differences to the
    last elections.

    """

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
                result.append(values.get('votes', {}).get('total', ''))
                permille = values.get('votes', {}).get('permille')
                result.append('{}%'.format(permille / 10 if permille else ''))
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
                            (values.get('votes', {}).get('permille', 0) or 0) -
                            (last.get('votes', {}).get('permille', 0) or 0)
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

    years, parties = get_party_results(item)
    names = sorted(parties.keys())

    results = []
    for party in names:
        for year in parties[party]:
            front = parties[party].get(year, {}).get('mandates', 0)
            back = parties[party].get(year, {}).get('votes', {})
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


@ElectionDayApp.json(
    model=Election,
    name='party-strengths-data',
    permission=Public
)
def view_election_party_strengths_data(self, request):

    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    return get_party_results_data(self)


@ElectionDayApp.html(
    model=Election,
    name='party-strengths-chart',
    template='embed.pt',
    permission=Public
)
def view_election_party_strengths_chart(self, request):

    """" View the party strengths as grouped bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'grouped_bar': request.link(self, name='party-strengths-data')
        }
    }


@ElectionDayApp.html(
    model=Election,
    name='party-strengths',
    template='election/party_strengths.pt',
    permission=Public
)
def view_election_party_strengths(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'party-strengths')

    years, parties = get_party_results(self)
    deltas, results = get_party_results_deltas(self, years, parties)

    return {
        'election': self,
        'layout': layout,
        'results': results,
        'years': years,
        'deltas': deltas
    }


@ElectionDayApp.json(
    model=Election,
    name='party-strengths-svg',
    permission=Public
)
def view_election_party_strengths_svg(self, request):

    """ View the party strengths as SVG. """

    layout = ElectionLayout(self, request, 'party-strengths')
    if not layout.svg_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.svg_path, 'r') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/svg; charset=utf-8',
        content_disposition='inline; filename={}'.format(layout.svg_name)
    )
