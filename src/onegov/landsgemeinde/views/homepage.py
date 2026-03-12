from __future__ import annotations

from morepath import redirect

from onegov.core.security import Public
from onegov.landsgemeinde.collections.assembly import AssemblyCollection
from onegov.landsgemeinde.models.assembly import Assembly
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.town6.layout import HomepageLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.html(
    model=Organisation,
    template='homepage.pt',
    permission=Public
)
def landsgemeinde_view_org(
    self: Organisation,
    request: LandsgemeindeRequest
) -> RenderData | Response:

    current_assembly = AssemblyCollection(request.session).query().filter(
        Assembly.state == 'ongoing').order_by(
        Assembly.date.desc()).first()

    if current_assembly:
        return redirect(request.link(current_assembly, name='ticker'))

    return view_org(self, request, HomepageLayout(self, request))
