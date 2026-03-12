from __future__ import annotations

from onegov.core.security import Public
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.layouts import DefaultLayout
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.swissvotes.request import SwissvotesRequest
    from webob import Response


@SwissvotesApp.html(
    model=HTTPForbidden,
    template='exception.pt',
    permission=Public
)
def handle_forbidden(
    self: HTTPForbidden,
    request: SwissvotesRequest
) -> RenderData:
    """ Displays a nice HTTP 403 error. """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Access Denied'),
        'message': _(
            'You are trying to open a page for which you are not authorized.'
        )
    }


@SwissvotesApp.html(
    model=HTTPNotFound,
    template='exception.pt',
    permission=Public
)
def handle_notfound(
    self: HTTPNotFound,
    request: SwissvotesRequest
) -> RenderData:
    """ Displays a nice HTTP 404 error. """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Page not Found'),
        'message': _('The page you are looking for could not be found.'),
    }
