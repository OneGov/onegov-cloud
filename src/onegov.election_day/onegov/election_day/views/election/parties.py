from onegov.ballot import Election
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

    year = str(election.date.year)
    years = [year]
    total_votes = election.accounted_votes
    parties = {
        party.name: {
            year: {
                'mandates': party.number_of_mandates,
                'votes': {
                    'total': party.votes,
                    'permille': int(round(1000 * (party.votes / total_votes)))
                }
            }
        }
        for party in election.party_results
    }

    historical = object_session(election).query(Election)
    historical = historical.filter(
        Election.type == 'proporz',
        Election.domain == election.domain,
        Election.number_of_mandates == election.number_of_mandates,
        Election.date < election.date
    )

    for past_election in historical:
        year = str(past_election.date.year)
        years.append(year)
        total_votes = election.accounted_votes
        for party in past_election.party_results:
            if party.name not in parties:
                parties[party.name] = {}
            parties[party.name][year] = {
                'mandates': party.number_of_mandates,
                'votes': {
                    'total': party.votes,
                    'permille': int(round(1000 * party.votes / total_votes))
                }
            }

    return sorted(set(years)), parties


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
            results.append({
                'group': party,
                'item': year,
                'value': {
                    'front': front,
                    'back': back,
                },
                'active': year == str(self.date.year)
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

    request.include('grouped_bar_chart')
    request.include('frame_resizer')

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

    request.include('grouped_bar_chart')
    request.include('tablesorter')

    handle_headerless_params(request)

    years, parties = get_party_results(self)
    results = []
    for party in sorted(parties.keys()):
        result = [party]
        for year in years:
            values = parties[party].get(year)
            if values:
                result.append(values.get('mandates', ''))
                permille = values.get('votes', {}).get('permille')
                result.append('{} / {}%'.format(
                    values.get('votes', {}).get('total', ''),
                    permille / 10 if permille else '',
                ))
            else:
                result.append('')
                result.append('')
        results.append(result)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'parties'),
        'results': results,
        'years': years
    }
