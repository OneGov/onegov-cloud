from __future__ import annotations

from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms import UserProfileForm
from onegov.org.models import Organisation
from onegov.town6.views.userprofile import town_handle_user_profile


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


@FeriennetApp.form(
    model=Organisation, name='userprofile', template='userprofile.pt',
    permission=Personal, form=UserProfileForm)
def handle_custom_user_profile(
    self: Organisation,
    request: FeriennetRequest,
    form: UserProfileForm
) -> RenderData | Response:
    return town_handle_user_profile(
        self, request, form)  # type:ignore
