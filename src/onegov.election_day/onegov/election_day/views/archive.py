from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Archive
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_summaries


@ElectionDayApp.html(model=Archive, template='homepage.pt', permission=Public)
def view_archive(self, request):

    results = self.by_date(group=False)
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

    results = self.by_date(group=False)
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
