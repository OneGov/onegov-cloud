from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal, Archive
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_summaries


@ElectionDayApp.html(model=Archive, template='archive.pt', permission=Public)
def view_archive(self, request):

    results = self.by_date()
    last_modified = self.last_modified(results)
    results = self.group_items(results)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, last_modified)

    return {
        'layout': DefaultLayout(self, request),
        'date': self.date,
        'archive_items': results
    }


@ElectionDayApp.json(model=Archive, permission=Public, name='json')
def view_archive_json(self, request):

    results = self.by_date()
    last_modified = self.last_modified(results)
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

    archive = Archive(request.app.session())
    latest = archive.latest()
    last_modified = archive.last_modified(latest)
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

    archive = Archive(request.app.session())
    latest = archive.latest()
    last_modified = archive.last_modified(latest)
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
