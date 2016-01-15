from onegov.core.security import Public
from onegov.onboarding import OnboardingApp
from onegov.onboarding.layout import DefaultLayout
from onegov.onboarding.models import Assistant


@OnboardingApp.html(model=Assistant, template='assistant.pt',
                    permission=Public)
def view_assistant(self, request):
    return {
        'title': self.title,
        'layout': DefaultLayout(self, request),
    }
