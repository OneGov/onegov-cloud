from __future__ import annotations

from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.exceptions import MTANAccessLimitExceeded
from onegov.org.layout import DefaultLayout
from onegov.user.auth import Auth
from webob.exc import HTTPForbidden, HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.html(model=HTTPForbidden, permission=Public, template='forbidden.pt')
def handle_forbidden(
    self: HTTPForbidden,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:
    """ If a view is forbidden, the request is redirected to the login
    view. There, the user may login to the site and be redirected back
    to the originally forbidden view.

    """

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code  # pass along 403

    layout = layout or DefaultLayout(self, request)

    return {
        'layout': layout,
        'title': _('Access Denied'),
        'login_url': request.link(
            Auth.from_request_path(request), name='login')
    }


@OrgApp.html(model=HTTPNotFound, permission=Public, template='notfound.pt')
def handle_notfound(
    self: HTTPNotFound,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code  # pass along 404

    return {
        'layout': layout or DefaultLayout(self, request),
        'title': _('Not Found'),
    }


@OrgApp.html(
    model=MTANAccessLimitExceeded,
    permission=Public,
    template='mtan_access_limit_exceeded.pt'
)
def handle_mtan_access_limit_exceeded(
    self: MTANAccessLimitExceeded,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = self.code  # pass along 423

    layout = layout or DefaultLayout(self, request)

    return {
        'layout': layout or DefaultLayout(self, request),
        'title': _('mTAN Access Limit Exceeded'),
    }
