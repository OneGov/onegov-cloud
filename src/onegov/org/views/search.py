import morepath

from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import Search, SearchPostgres
from onegov.search import SearchOfflineError
from webob import exc


@OrgApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request, layout=None):
    print('*** tschupre org search')

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Search"), '#'))

    try:
        searchlabel = _("Search through ${count} indexed documents", mapping={
            'count': self.available_documents
        })
        resultslabel = _("${count} Results", mapping={
            'count': self.subset_count
        })
    except SearchOfflineError:
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


@OrgApp.html(model=SearchPostgres, template='search_postgres.pt',
             permission=Public)
def search_postgres(self, request, layout=None):
    print('*** tschupre org search postgres')

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Search"), '#'))

    try:
        searchlabel = _("Search through ${count} indexed documents", mapping={
            'count': self.available_documents
        })
        resultslabel = _("${count} Results", mapping={
            'count': self.available_results
        })
    except SearchOfflineError:
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
        'title': _("Org Search Postgres"),
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
        print('*** tschupre suggestions_es')
        return tuple(self.suggestions())
    except SearchOfflineError as exception:
        raise exc.HTTPNotFound() from exception


@OrgApp.json(model=SearchPostgres, name='suggest', permission=Public)
def suggestions_postgres(self, request):
    try:
        print('*** tschupre suggestions_postgres')
        return tuple(self.suggestions_postgres())
    except SearchOfflineError as exception:
        raise exc.HTTPNotFound() from exception
