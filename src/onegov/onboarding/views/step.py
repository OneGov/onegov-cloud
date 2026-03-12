from __future__ import annotations

import morepath

from onegov.core.security import Public
from onegov.onboarding import _
from onegov.onboarding import OnboardingApp
from onegov.onboarding.layout import DefaultLayout
from onegov.onboarding.models import Assistant, DefaultAssistant
from webob.exc import HTTPMethodNotAllowed


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from onegov.form import Form
    from webob import Response


@OnboardingApp.view(model=DefaultAssistant, permission=Public)
def view_default_assistant(
    self: DefaultAssistant,
    request: CoreRequest
) -> Response:
    return morepath.redirect(request.link(self.assistant))


@OnboardingApp.form(
    model=Assistant,
    template='step.pt',
    permission=Public,
    form=lambda model, request: model.current_step.form
)
def view_assistant(
    self: Assistant,
    request: CoreRequest,
    form: Form | None
) -> RenderData | Response:

    # usually this is morepath's job, but we're doing some funny things here ;)
    if form is None and request.method == 'POST':
        return HTTPMethodNotAllowed()

    response = self.current_step.handle_view(request, form)

    if isinstance(response, dict):
        assert 'layout' not in response
        response['layout'] = DefaultLayout(self, request)

        if 'form' not in response:
            response['form'] = form

        if self.is_last_step:
            response['button_text'] = _('Launch')
        else:
            response['button_text'] = _('Continue')

    return response
