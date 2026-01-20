from __future__ import annotations

from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from webob.exc import HTTPAccepted
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=HTTPForbidden,
    template='exception.pt',
    permission=Public
)
def handle_forbidden(
    self: HTTPForbidden,
    request: ElectionDayRequest
) -> RenderData:

    """ Displays a nice HTTP 403 error. """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code  # pass along 403

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Access Denied'),
        'message': _(
            'You are trying to open a page for which you are not authorized.'
        )
    }


@ElectionDayApp.html(
    model=HTTPNotFound,
    template='exception.pt',
    permission=Public
)
def handle_notfound(
    self: HTTPNotFound,
    request: ElectionDayRequest
) -> RenderData:

    """ Displays a nice HTTP 404 error. """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code  # pass along 404

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Page not Found'),
        'message': _('The page you are looking for could not be found.'),
    }


@ElectionDayApp.html(
    model=HTTPAccepted,
    template='exception.pt',
    permission=Public
)
def handle_accepted(
    self: HTTPAccepted,
    request: ElectionDayRequest
) -> RenderData:

    """ Displays a nice HTTP 202 exception. """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _('File not yet ready'),
        'message': _(
            'The file you are looking for is not ready yet. '
            'Please try again later.'
        ),
    }
