from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.ballot import VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.html(model=Principal, template='homepage.pt',
                     permission=Public)
def view_principal(self, request):

    collection = VoteCollection(request.app.session())
    votes = collection.get_latest()

    if votes:
        votes_by_domain_and_date = groupbylist(
            votes, lambda v: (v.domain, v.date))
    else:
        votes_by_domain_and_date = None

    return {
        'layout': DefaultLayout(self, request),
        'votes_by_domain_and_date': votes_by_domain_and_date
    }
