from morepath.request import Response
from onegov.ballot import Election
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_vote(self, request):

    layout = DefaultLayout(self, request)
    request.include('bar_chart')

    lists = sorted(
        self.list_results, key=lambda x: (x[2], x[1]), reverse=True
    )
    candidates = self.candidate_results
    candidates_sorted = sorted(
        candidates, key=lambda x: (x[3], x[5]), reverse=True
    )

    return {
        'election': self,
        'layout': layout,
        'lists': lists,
        'candidates': candidates,
        'candidates_sorted': candidates_sorted
    }


@ElectionDayApp.json(model=Election, name='json', permission=Public)
def view_vote_as_json(self, request):
    return self.export()


@ElectionDayApp.view(model=Election, name='csv', permission=Public)
def view_vote_as_csv(self, request):
    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Election, name='xlsx', permission=Public)
def view_vote_as_xlsx(self, request):
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
    return [
        dict((
            ('text', result[0]),
            ('value', result[1]),
            ('class', 'active' if result[2] else 'inactive')
        ))
        for result in sorted(
            self.candidate_results, key=lambda x: (x[2], x[1]), reverse=True
        )
        if result[1] > self.accounted_votes / 100
    ]
