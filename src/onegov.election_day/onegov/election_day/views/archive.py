from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_summaries


@ElectionDayApp.html(
    model=ArchivedResultCollection,
    template='archive.pt',
    permission=Public
)
def view_archive(self, request):

    """ Shows all the results from the elections and votes for a given year
    or date.

    """

    layout = DefaultLayout(self, request)
    results, last_modified = self.by_date()
    results = self.group_items(results, request)

    return {
        'layout': layout,
        'date': self.date,
        'archive_items': results
    }


@ElectionDayApp.json(
    model=ArchivedResultCollection,
    name='json',
    permission=Public
)
def view_archive_json(self, request):

    """ Shows all the results from the elections and votes for a given year
    or date as JSON.

    """

    results, last_modified = self.by_date()
    results = get_summaries(results, request)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'canton': request.app.principal.id,
        'name': request.app.principal.name,
        'results': results,
        'archive': get_archive_links(self, request)
    }


@ElectionDayApp.html(
    model=Principal,
    template='archive.pt',
    permission=Public
)
def view_principal(self, request):

    """ Shows all the results from the elections and votes of the last election
    day.

    """

    layout = DefaultLayout(self, request)
    archive = ArchivedResultCollection(request.session)
    latest, last_modified = archive.latest()
    latest = archive.group_items(latest, request)

    return {
        'layout': layout,
        'archive_items': latest,
        'date': None
    }


@ElectionDayApp.json(
    model=Principal,
    name='json',
    permission=Public
)
def view_principal_json(self, request):

    """ Shows all the results from the elections and votes of the last election
    day as JSON.

    """

    archive = ArchivedResultCollection(request.session)
    latest, last_modified = archive.latest()
    latest = get_summaries(latest, request)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'canton': self.id,
        'name': self.name,
        'results': latest,
        'archive': get_archive_links(archive, request)
    }
