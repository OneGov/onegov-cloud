from onegov.core.security import Public, Private
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal
from onegov.election_day.collection import ArchivedResultCollection
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_summaries


@ElectionDayApp.html(model=ArchivedResultCollection, template='archive.pt',
                     permission=Public)
def view_archive(self, request):

    results, last_modified = self.by_date()
    results = self.group_items(results)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'layout': DefaultLayout(self, request),
        'date': self.date,
        'archive_items': results
    }


@ElectionDayApp.json(model=ArchivedResultCollection, permission=Public,
                     name='json')
def view_archive_json(self, request):

    results, last_modified = self.by_date()
    results = get_summaries(results, request)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'canton': request.app.principal.canton,
        'name': request.app.principal.name,
        'results': results,
        'archive': get_archive_links(self, request)
    }


@ElectionDayApp.html(model=Principal, template='archive.pt', permission=Public)
def view_principal(self, request):

    archive = ArchivedResultCollection(request.app.session())
    latest, last_modified = archive.latest()
    latest = archive.group_items(latest, reverse=True)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'layout': DefaultLayout(self, request),
        'archive_items': latest,
        'date': None,
        'show_base_link': True
    }


@ElectionDayApp.json(model=Principal, permission=Public, name='json')
def view_principal_json(self, request):

    archive = ArchivedResultCollection(request.app.session())
    latest, last_modified = archive.latest()
    latest = get_summaries(latest, request)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'canton': self.canton,
        'name': self.name,
        'results': latest,
        'archive': get_archive_links(archive, request)
    }


@ElectionDayApp.json(model=Principal, permission=Private,
                     name='update-results')
def view_update_results(self, request):

    archive = ArchivedResultCollection(request.app.session())
    archive.update_all(request)

    return {'result': 'ok'}
