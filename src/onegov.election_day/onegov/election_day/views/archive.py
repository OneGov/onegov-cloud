from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.ballot import VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout


@ElectionDayApp.html(model=VoteCollection, template='archive.pt',
                     permission=Public)
def view_archive(self, request):

    votes = self.by_year()

    if votes:
        votes_by_domain_and_date = groupbylist(
            votes, lambda v: (v.domain, v.date))
    else:
        votes_by_domain_and_date = None

    return {
        'layout': DefaultLayout(self, request),
        'year': self.year,
        'votes_by_domain_and_date': votes_by_domain_and_date
    }
