from __future__ import annotations

from onegov.core.security import Personal, Public

from onegov.org.views.userprofile import (
    handle_user_profile, handle_unsubscribe)
from onegov.town6.app import TownApp
from onegov.org.forms import UserProfileForm
from onegov.org.models import Organisation
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=Organisation,
    name='userprofile',
    template='userprofile.pt',
    permission=Personal,
    form=UserProfileForm
)
def town_handle_user_profile(
    self: Organisation,
    request: TownRequest,
    form: UserProfileForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    return handle_user_profile(
        self, request, form, layout or DefaultLayout(self, request)
    )


# the view name must remain english, so that automated tools can detect it
@TownApp.html(
    model=Organisation,
    name='unsubscribe',
    template='unsubscribe.pt',
    permission=Public
)
def town_handle_unsubscribe(
    self: Organisation,
    request: TownRequest
) -> RenderData | Response:
    return handle_unsubscribe(self, request, DefaultLayout(self, request))
