from onegov.ballot import Ballot, Vote
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote(self, request):

    layout = DefaultLayout(self, request)
    request.include('ballot_map')

    return {
        'vote': self,
        'layout': layout,
    }


@ElectionDayApp.json(model=Ballot, permission=Public, name='by-municipality')
def view_ballot_by_municipality(self, request):
    return self.percentage_by_municipality()
