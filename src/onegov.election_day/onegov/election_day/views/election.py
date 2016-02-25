from morepath.request import Response
from onegov.ballot import (
    Candidate,
    CandidateResult,
    Election,
    ElectionResult,
    List,
    ListConnection
)
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from sqlalchemy import desc
from sqlalchemy.orm import object_session


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_election(self, request):

    layout = DefaultLayout(self, request)
    request.include('bar_chart')

    majorz = self.type == 'majorz'
    session = object_session(self)

    # Candidates: Overview
    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes,
        List.name,
    )
    candidates = candidates.outerjoin(List)
    candidates = candidates.order_by(
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == self.id)

    # Candidates: Electoral results
    electoral = []
    if majorz:
        electoral = session.query(ElectionResult.group, CandidateResult.votes)
        electoral = electoral.outerjoin(CandidateResult, Candidate)
        electoral = electoral.order_by(
            ElectionResult.group,
            Candidate.candidate_id
        )
        electoral = electoral.filter(ElectionResult.election_id == self.id)
        electoral = groupbylist(electoral, key=lambda x: x[0])

    # List results
    lists = []
    if not majorz:
        lists = session.query(
            List.name,
            List.votes,
            List.number_of_mandates,
        )
        lists = lists.order_by(
            desc(List.number_of_mandates),
            desc(List.votes),
            List.name,
        )
        lists = lists.filter(List.election_id == self.id)

    # List connections
    connections = []
    if not majorz:
        connections = self.list_connections.filter_by(parent_id=None)

    return {
        'election': self,
        'layout': layout,
        'majorz': majorz,
        'has_results': True if self.results.first() else False,
        'candidates': candidates,
        'electoral': electoral,
        'lists': lists,
        'connections': connections,
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
