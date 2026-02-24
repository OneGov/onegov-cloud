from __future__ import annotations

from onegov.core.security import Public
from onegov.winterthur import WinterthurApp, _
from onegov.org.layout import DefaultLayout
from onegov.winterthur.roadwork import RoadworkConnectionError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.winterthur.request import WinterthurRequest
    from webob import Response


@WinterthurApp.html(
    model=RoadworkConnectionError,
    permission=Public,
    template='roadwork_connection_error.pt')
def handle_roadwork_connection_error(
    self: RoadworkConnectionError,
    request: WinterthurRequest
) -> RenderData:

    @request.after
    def set_status_code(response: Response) -> None:
        response.status_code = 500

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Connection Error'),
    }
