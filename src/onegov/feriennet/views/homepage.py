from __future__ import annotations

from onegov.core.security import Public
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.feriennet import FeriennetApp
from onegov.feriennet.layout import HomepageLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


@FeriennetApp.html(
    model=Organisation,
    template='homepage.pt',
    permission=Public
)
def feriennet_view_org(
    self: Organisation,
    request: FeriennetRequest
) -> RenderData | Response:
    return view_org(self, request, HomepageLayout(self, request))
