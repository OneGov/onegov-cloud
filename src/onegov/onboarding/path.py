from onegov.onboarding import OnboardingApp
from onegov.onboarding.models import DefaultAssistant, TownAssistant


@OnboardingApp.path(model=DefaultAssistant, path='/')
def get_default_assistant(app):
    return DefaultAssistant(TownAssistant(app))


@OnboardingApp.path(model=TownAssistant,
                    path='/for-towns/{current_step_number}')
def get_town_assistant(app, current_step_number=1):
    try:
        return TownAssistant(app, current_step_number)
    except KeyError:
        return None
