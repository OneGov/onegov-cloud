from __future__ import annotations

import morepath

from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import Search
from onegov.org.models.search import SearchPostgres
from onegov.search import SearchOfflineError
from webob import exc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.html(model=Search, template='search.pt', permission=Public)
def search(
    self: Search[Base],
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
        resultslabel = _('${count} Results', mapping={
            'count': self.subset_count
        })
    except SearchOfflineError:
        return {
            'title': _('Search Unavailable'),
            'layout': layout,
            'connection': False
        }

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


@OrgApp.html(model=SearchPostgres, template='search_postgres.pt',
             permission=Public)
def search_postgres(
    self: SearchPostgres[Base],
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
        resultslabel = _('${count} Results', mapping={
            'count': self.available_results
        })
    except SearchOfflineError:
        return {
            'title': _('Search Unavailable'),
            'layout': layout,
            'connection': False
        }

    if 'lucky' in request.GET:
        url = self.feeling_lucky()

        if url:
            return morepath.redirect(url)

    return {
        # TODO switch back to 'Search' once es is gone
        'title': _('Org Search Postgres'),
        'model': self,
        'layout': layout,
        'hide_search_header': True,
        'searchlabel': searchlabel,
        'resultslabel': resultslabel,
        'connection': True
    }


@OrgApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self: Search[Base], request: OrgRequest) -> JSON_ro:
    try:
        return self.suggestions()
    except SearchOfflineError as exception:
        raise exc.HTTPNotFound() from exception


@OrgApp.json(model=SearchPostgres, name='suggest', permission=Public)
def suggestions_postgres(self: SearchPostgres[Base], request: OrgRequest) \
        -> JSON_ro:
    try:
        return self.suggestions()
    except SearchOfflineError as exception:
        raise exc.HTTPNotFound() from exception
