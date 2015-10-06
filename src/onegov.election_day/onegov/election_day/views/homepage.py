from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.ballot import VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.html(model=Principal, template='homepage.pt',
                     permission=Public)
def view_principal(self, request):

    votes = VoteCollection(request.app.session()).get_latest()

    if votes:
        votes_by_domain = groupbylist(votes, lambda v: v.domain)
    else:
        votes_by_domain = None

    return {
        'votes_by_domain': votes_by_domain,
        'layout': DefaultLayout(self, request),
    }
