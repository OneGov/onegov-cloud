from morepath.request import Response
from onegov.ballot import Election
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_election(self, request):

    layout = DefaultLayout(self, request)
    request.include('bar_chart')

    lists = sorted(self.lists, key=lambda x: x.name)
    lists.sort(key=lambda x: (x.number_of_mandates, x.votes), reverse=True)

    connections = self.list_connections.filter_by(parent_id=None)

    candidates = sorted(self.candidates, key=lambda x: (x.family_name))
    candidates.sort(key=lambda x: (x.elected, x.votes), reverse=True)

    return {
        'election': self,
        'layout': layout,
        'has_results': True if self.results.first() else False,
        'lists': lists,
        'connections': connections,
        'candidates': candidates,
    }


@ElectionDayApp.json(model=Election, name='json', permission=Public)
def view_election_as_json(self, request):
    return self.export()


@ElectionDayApp.view(model=Election, name='csv', permission=Public)
def view_election_as_csv(self, request):
    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Election, name='xlsx', permission=Public)
def view_election_as_xlsx(self, request):
    return Response(
        convert_list_of_dicts_to_xlsx(self.export()),
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename={}.xlsx'.format(
            normalize_for_url(self.title)
        )
    )


@ElectionDayApp.json(model=Election, permission=Public, name='candidates')
def view_election_candidates(self, request):
    result = [{
        'text': '{} {}'.format(c.family_name, c.first_name),
        'value': c.votes,
        'class': 'active' if c.elected else 'inactive'
    } for c in self.candidates if c.votes > self.accounted_votes / 100]
    result.sort(key=lambda x: x['value'], reverse=True)
    result.sort(key=lambda x: x['class'])
    return result
