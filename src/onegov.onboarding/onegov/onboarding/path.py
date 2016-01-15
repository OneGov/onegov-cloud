from onegov.onboarding import OnboardingApp
from onegov.onboarding.models import DefaultAssistant, TownAssistant


@OnboardingApp.path(model=DefaultAssistant, path='/')
def get_default_assistant():
    return DefaultAssistant(TownAssistant())


@OnboardingApp.path(model=TownAssistant,
                    path='/for-towns/{current_step_number}')
def get_town_assistant(current_step_number=1):
    try:
        return TownAssistant(current_step_number)
    except KeyError:
        return None
