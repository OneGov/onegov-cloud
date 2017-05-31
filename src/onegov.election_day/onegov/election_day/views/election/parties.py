from morepath.request import Response
from onegov.ballot import Election
from onegov.ballot import PartyResult
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout, ElectionsLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import handle_headerless_params
from sqlalchemy.orm import object_session


def get_party_results(election):
    """ Returns the aggregated party results as list. """

    if election.type != 'proporz' or not election.party_results.first():
        return [], {}

    session = object_session(election)

    # Get the totals votes per year
    query = session.query(PartyResult.year, PartyResult.total_votes)
    query = query.filter(PartyResult.election_id == election.id).distinct()
    totals = dict(query)
    years = sorted((str(key) for key in totals.keys()))

    parties = {}
    for result in election.party_results:
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


def get_party_deltas(election, years, parties):
    """ Returns the aggregated party results with the differences to the
    last elections.

    """

    deltas = len(years) > 1
    results = []
    for key in sorted(parties.keys()):
        result = [key]
        party = parties[key]
        for year in years:
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
            now = party.get(years[-1])
            then = party.get(years[-2])
            if now and then:
                result.append('{}%'.format(
                    ((now.get('votes', {}).get('permille', 0) or 0) -
                     (then.get('votes', {}).get('permille', 0) or 0)) / 10
                ))
            else:
                result.append('')

        results.append(result)

    return deltas, results


@ElectionDayApp.json(model=Election, permission=Public,
                     name='parties-data')
def view_election_parties_data(self, request):

    if self.type == 'majorz':
        return {
            'results': [],
            'title': self.title
        }

    years, parties = get_party_results(self)
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
                'active': year == str(self.date.year),
                'color': color
            })

    return {
        'groups': names,
        'labels': years,
        'maximum': {
            'front': self.number_of_mandates,
            'back': 100,
        },
        'axis_units': {
            'front': '',
            'back': '%'
        },
        'results': results,
        'title': self.title
    }


@ElectionDayApp.html(model=Election, permission=Public,
                     name='parties-chart', template='embed.pt')
def view_election_parties_chart(self, request):
    """" View the parties as grouped bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'grouped_bar': request.link(self, name='parties-data')
        }
    }


@ElectionDayApp.html(model=Election, template='election/parties.pt',
                     name='parties', permission=Public)
def view_election_parties(self, request):
    """" The main view. """

    handle_headerless_params(request)

    years, parties = get_party_results(self)
    deltas, results = get_party_deltas(self, years, parties)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'parties'),
        'results': results,
        'years': years,
        'deltas': deltas
    }


@ElectionDayApp.json(model=Election, permission=Public, name='parties-svg')
def view_election_parties_svg(self, request):
    """ View the parties as SVG. """

    layout = ElectionsLayout(self, request, 'parties')
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
