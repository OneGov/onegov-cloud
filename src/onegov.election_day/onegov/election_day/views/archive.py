from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Archive


@ElectionDayApp.html(model=Archive, template='homepage.pt', permission=Public)
def view_archive(self, request):

    results = self.by_date(group=False)
    last_modified = self.last_modified(results)
    results = self.group_items(results)

    @request.after
    def add_last_modified(response):
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )

    return {
        'layout': DefaultLayout(self, request),
        'date': self.date,
        'archive_items': results
    }


@ElectionDayApp.json(model=Archive, permission=Public, name='json')
def view_archive_json(self, request):

    results = self.by_date(group=False)
    last_modified = self.last_modified(results)
    results = self.to_json(results, request)

    @request.after
    def add_last_modified(response):
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )

    return {
        'canton': request.app.principal.canton,
        'name': request.app.principal.name,
        'results': results
    }
