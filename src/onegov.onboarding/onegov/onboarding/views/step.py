import morepath

from onegov.core.security import Public
from onegov.onboarding import OnboardingApp
from onegov.onboarding.layout import DefaultLayout
from onegov.onboarding.models import Assistant, DefaultAssistant


@OnboardingApp.view(model=DefaultAssistant, permission=Public)
def view_default_assistant(self, request):
    return morepath.redirect(request.link(self.assistant))


@OnboardingApp.html(model=Assistant, template='step.pt', permission=Public)
def view_assistant(self, request):
    response = self.current_step.handle_view(request)

    if isinstance(response, dict):
        assert 'layout' not in response
        response['layout'] = DefaultLayout(self, request)

    return response
