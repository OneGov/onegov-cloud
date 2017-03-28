import morepath

from elasticsearch import TransportError
from onegov.core.security import Public
from onegov.org import _, log, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import Search
from webob import exc


@OrgApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Search"), '#'))

    try:
        searchlabel = _("Search through ${count} indexed documents", mapping={
            'count': self.available_documents
        })
        resultslabel = _("${count} Results", mapping={
            'count': self.subset_count
        })
    except TransportError:
        log.exception("Elasticsearch cluster is offline")
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
        'searchlabel': searchlabel,
        'resultslabel': resultslabel,
        'connection': True
    }


@OrgApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self, request):
    try:
        return tuple(self.suggestions())
    except TransportError:
        raise exc.HTTPNotFound()
