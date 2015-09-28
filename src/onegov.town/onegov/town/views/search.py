import morepath

from elasticsearch import TransportError
from onegov.core.security import Public
from onegov.town import _, log, TownApp
from onegov.town.elements import Link
from onegov.town.models import Search
from onegov.town.layout import DefaultLayout
from webob import exc


@TownApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Search"), '#'))

    try:
        request.app.es_client.ping()
        log.warn("Elasticsearch cluster is offline")
    except TransportError:
        return {
            'title': _("Search Unavailable"),
            'layout': layout,
            'connection': False
        }

    if 'lucky' in request.GET:
        url = self.feeling_lucky()

        if url:
            return morepath.redirect(url)

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
        }),
        'connection': True
    }


@TownApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self, request):
    try:
        return tuple(self.suggestions())
    except TransportError:
        raise exc.HTTPNotFound()
