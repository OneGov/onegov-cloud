from onegov.core.security import Public
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.layouts import DefaultLayout
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from webob.response import Response


@WtfsApp.html(
    model=HTTPForbidden,
    template='exception.pt',
    permission=Public
)
def handle_forbidden(
    self: HTTPForbidden,
    request: 'CoreRequest'
) -> 'RenderData':
    """ Displays a nice HTTP 403 error. """

    @request.after
    def set_status_code(response: 'Response') -> None:
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Access Denied"),
        'message': _(
            "You are trying to open a page for which you are not authorized."
        )
    }


@WtfsApp.html(
    model=HTTPNotFound,
    template='exception.pt',
    permission=Public
)
def handle_notfound(
    self: HTTPNotFound,
    request: 'CoreRequest'
) -> 'RenderData':
    """ Displays a nice HTTP 404 error. """

    @request.after
    def set_status_code(response: 'Response') -> None:
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Page not Found"),
        'message': _("The page you are looking for could not be found."),
    }
