from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.model import Principal


@ElectionDayApp.html(model=Principal, template='homepage.pt',
                     permission=Public)
def view_principal(self, request):
    return {
        'layout': DefaultLayout(self, request)
    }
