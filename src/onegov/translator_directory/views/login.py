from __future__ import annotations

from onegov.core.security import Public
from onegov.town6.views.auth import town_handle_login as handle_login_base
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.login import LoginForm
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=LoginForm
)
def handle_login(
    self: Auth,
    request: TranslatorAppRequest,
    form: LoginForm
) -> RenderData | Response:

    # custom username handle
    form.username.label.text = request.translate(
        _('E-Mail Address / Username / Shortcut')
    )

    return handle_login_base(self, request, form)
