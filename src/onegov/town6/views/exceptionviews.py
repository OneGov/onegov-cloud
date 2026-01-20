from __future__ import annotations

from onegov.core.security import Public
from onegov.org.views.exceptionviews import handle_forbidden, handle_notfound
from onegov.town6 import TownApp
from webob.exc import HTTPForbidden, HTTPNotFound

from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(model=HTTPForbidden, permission=Public, template='forbidden.pt')
def town_handle_forbidden(
    self: HTTPForbidden,
    request: TownRequest
) -> RenderData:
    return handle_forbidden(self, request, DefaultLayout(self, request))


@TownApp.html(model=HTTPNotFound, permission=Public, template='notfound.pt')
def town_handle_notfound(
    self: HTTPNotFound,
    request: TownRequest
) -> RenderData:
    return handle_notfound(self, request, DefaultLayout(self, request))
