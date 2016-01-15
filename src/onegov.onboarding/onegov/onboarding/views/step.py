from onegov.core.security import Public
from onegov.onboarding import OnboardingApp
from onegov.onboarding.layout import DefaultLayout
from onegov.onboarding.models import Assistant, Step


@OnboardingApp.html(model=Assistant, template='step.pt', permission=Public)
def view_assistant(self, request):
    return view_step(self.steps[0], request)


@OnboardingApp.html(model=Step, template='step.pt', permission=Public)
def view_step(self, request):
    response = self.handle_view(request)

    if isinstance(response, dict):
        assert 'layout' not in response
        response['layout'] = DefaultLayout(self, request)

    return response
