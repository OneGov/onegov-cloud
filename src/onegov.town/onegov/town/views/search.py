from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.models import Search
from onegov.town.layout import DefaultLayout


@TownApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):
    return {
        'title': _("Search"),
        'model': self,
        'layout': DefaultLayout(self, request),
        'searchlabel': _("Search through ${count} indexed documents", mapping={
            'count': self.available_documents
        }),
        'resultslabel': _("${count} Results", mapping={
            'count': len(self.batch)
        })
    }
