from __future__ import annotations

from onegov.user.auth.core import Auth
from onegov.pas.app import PasApp
from onegov.core.security import Public
from onegov.org.models import Organisation
from morepath import redirect


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.view(model=Organisation, permission=Public)
def view_org(
    self: Organisation,
    request: TownRequest
) -> Response:
    """ Renders the homepage. """

    if not request.is_logged_in:
        return redirect(request.class_link(Auth, name='login'))

    return redirect(request.class_link(Organisation, name='pas-settings'))
