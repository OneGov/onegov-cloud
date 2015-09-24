import morepath

from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.models import Search
from onegov.town.layout import DefaultLayout


@TownApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):

    if 'lucky' in request.GET:
        url = self.feeling_lucky()

        if url:
            return morepath.redirect(url)

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Search"), '#'))

    return {
        'title': _("Search"),
        'model': self,
        'layout': layout,
        'hide_search_header': True,
        'searchlabel': _("Search through ${count} indexed documents", mapping={
            'count': self.available_documents
        }),
        'resultslabel': _("${count} Results", mapping={
            'count': self.subset_count
        })
    }


@TownApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self, request):
    return tuple(self.suggestions())
