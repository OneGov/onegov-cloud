from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal, Archive


@ElectionDayApp.html(model=Principal, template='homepage.pt',
                     permission=Public)
def view_principal(self, request):

    return {
        'layout': DefaultLayout(self, request),
        'archive_items': Archive(request.app.session()).latest(),
        'show_base_link': True
    }


@ElectionDayApp.json(model=Principal, permission=Public, name='json')
def view_principal_json(self, request):

    return {
        'canton': self.canton,
        'name': self.name,
        'results': Archive(request.app.session()).latest_json(request)
    }


@ElectionDayApp.html(model=Principal, template='opendata.pt', name='opendata',
                     permission=Public)
def view_opendata(self, request):
    return {
        'layout': DefaultLayout(self, request),
    }
