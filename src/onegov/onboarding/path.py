from __future__ import annotations

from onegov.onboarding import OnboardingApp
from onegov.onboarding.models import DefaultAssistant, TownAssistant


@OnboardingApp.path(model=DefaultAssistant, path='/')
def get_default_assistant(app: OnboardingApp) -> DefaultAssistant:
    return DefaultAssistant(TownAssistant(app))


@OnboardingApp.path(
    model=TownAssistant,
    path='/for-towns/{current_step_number}'
)
def get_town_assistant(
    app: OnboardingApp,
    current_step_number: int = 1
) -> TownAssistant | None:
    try:
        return TownAssistant(app, current_step_number)
    except KeyError:
        return None
