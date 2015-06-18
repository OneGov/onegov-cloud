from onegov.core.security import Public
from onegov.ballot import Vote
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote(self, request):

    return {
        'vote': self,
        'layout': DefaultLayout(self, request),
    }
