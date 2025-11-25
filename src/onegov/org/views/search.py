from __future__ import annotations

import morepath
import transaction

from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import Search
from onegov.search import SearchOfflineError
from sqlalchemy.exc import InternalError
from webob import exc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.html(model=Search, template='search.pt', permission=Public)
def search(
    self: Search,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    layout = layout or DefaultLayout(self, request)
    assert isinstance(layout.breadcrumbs, list)
    layout.breadcrumbs.append(Link(_('Search'), '#'))

    try:
        searchlabel = _('Search through ${count} indexed documents', mapping={
            'count': self.available_documents
        })
    except SearchOfflineError:
        return {
            'title': _('Search Unavailable'),
            'layout': layout,
            'connection': False
        }
    try:
        available_results = self.available_results
    except InternalError:
        # reset transaction machinery so our transaction is no longer doomed
        transaction.abort()
        transaction.begin()
        # probably some malicious search term, that tried to burn CPU cycles
        # we just pretend we succeeded but return no results
        available_results = self.__dict__['available_results'] = 0
        self.__dict__['subset_count'] = 0
        self.__dict__['batch'] = ()

    resultslabel = _('${count} Results', mapping={
        'count': available_results
    })

    if 'lucky' in request.GET:
        url = self.feeling_lucky()

        if url:
            return morepath.redirect(url)

    return {
        'title': _('Search'),
        'model': self,
        'layout': layout,
        'hide_search_header': True,
        'searchlabel': searchlabel,
        'resultslabel': resultslabel,
        'connection': True
    }


@OrgApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self: Search, request: OrgRequest) -> JSON_ro:
    try:
        return self.suggestions()
    except SearchOfflineError as exception:
        raise exc.HTTPNotFound() from exception
