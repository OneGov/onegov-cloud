from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal, Archive


@ElectionDayApp.html(model=Principal, template='homepage.pt',
                     permission=Public)
def view_principal(self, request):

    archive = Archive(request.app.session())
    latest = archive.latest(group=False)
    last_modified = archive.last_modified(latest)
    latest = archive.group_items(latest, reverse=True)

    @request.after
    def add_last_modified(response):
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )

    return {
        'layout': DefaultLayout(self, request),
        'archive_items': latest,
        'show_base_link': True
    }


@ElectionDayApp.json(model=Principal, permission=Public, name='json')
def view_principal_json(self, request):

    archive = Archive(request.app.session())
    latest = archive.latest(group=False)
    last_modified = archive.last_modified(latest)
    latest = archive.to_json(latest, request)

    @request.after
    def add_last_modified(response):
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )

    return {
        'canton': self.canton,
        'name': self.name,
        'results': latest
    }


@ElectionDayApp.html(model=Principal, template='opendata.pt', name='opendata',
                     permission=Public)
def view_opendata(self, request):
    return {
        'layout': DefaultLayout(self, request),
    }
