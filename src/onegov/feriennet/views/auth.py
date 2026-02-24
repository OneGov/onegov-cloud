from __future__ import annotations

from onegov.core.security import Public
from onegov.feriennet import FeriennetApp, _
from onegov.town6.views.auth import town_handle_registration
from onegov.user import Auth
from onegov.user.forms import RegistrationForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


@FeriennetApp.form(
    model=Auth, name='register', template='form.pt',
    permission=Public, form=RegistrationForm
)
def custom_handle_registration(
    self: Auth,
    request: FeriennetRequest,
    form: RegistrationForm
) -> RenderData | Response:

    if request.app.org.meta.get('require_full_age_for_registration', False):
        form.callout = _(  # type:ignore[attr-defined]
            'The user account must be opened by a parent or guardian of '
            'full age.'
        )
    return town_handle_registration(self, request, form)
