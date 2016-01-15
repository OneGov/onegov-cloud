from onegov.onboarding import OnboardingApp
from onegov.onboarding.models import Assistant, TownAssistant


@OnboardingApp.path(model=Assistant, path='/')
def get_default_assistant(object):
    return get_town_assistant()


@OnboardingApp.path(model=TownAssistant, path='/for-towns')
def get_town_assistant():
    return TownAssistant()
