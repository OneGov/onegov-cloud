from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.forms import ArchiveSearchFormElection
from onegov.election_day.forms import ArchiveSearchFormVote
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts.archive import ArchiveLayout
from onegov.election_day.models import Principal
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
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
    archive_link = request.class_link(
        SearchableArchivedResultCollection,
        variables={'item_type': 'vote'}
    )

    return {
        'layout': layout,
        'date': self.date,
        'archive_items': results,
        'archive_link': archive_link
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
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    return {
        'canton': request.app.principal.id,
        'name': request.app.principal.name,
        'results': results,
        'archive': {
            str(year): request.link(self.for_date(year))
            for year in self.get_years()
        }
    }


@ElectionDayApp.html(
    model=Principal,
    template='archive.pt',
    permission=Public
)
def view_principal(self, request):

    """ Shows all the results from the elections and votes of the last election
    day. It's the landing page.

    """

    layout = DefaultLayout(self, request)
    archive = ArchivedResultCollection(request.session)
    latest, last_modified = archive.latest()
    latest = archive.group_items(latest, request)
    archive_link = request.class_link(
        SearchableArchivedResultCollection,
        variables={'item_type': 'vote'}
    )

    return {
        'layout': layout,
        'archive_items': latest,
        'date': None,
        'archive_link': archive_link
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
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    return {
        'canton': self.id,
        'name': self.name,
        'results': latest,
        'archive': {
            str(year): request.link(archive.for_date(year))
            for year in archive.get_years()
        }
    }


def search_form(model, request, form=None):
    if model.item_type == 'vote':
        return ArchiveSearchFormVote
    return ArchiveSearchFormElection


@ElectionDayApp.form(
    model=SearchableArchivedResultCollection,
    template='archive_search.pt',
    form=search_form,
    permission=Public,
)
def view_archive_search(self, request, form):

    """ Shows all the results from the elections and votes of the last election
    day. It's the landing page.
    """

    layout = ArchiveLayout(self, request)
    self.locale = request.locale

    if not form.errors:
        form.apply_model(self)

    return {
        'item_type': self.item_type,
        'layout': layout,
        'form': form,
        'form_method': 'GET',
        'item_count': self.subset_count,
        'results': self.batch
    }
