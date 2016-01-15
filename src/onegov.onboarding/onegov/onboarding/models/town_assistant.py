from onegov.onboarding import _
from onegov.onboarding.models.assistant import Assistant


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town onboarding. """

    title = _("Test OneGov Cloud now")

    @Assistant.step
    def first_step(self, request):
        return {
            'title': _("Run your town's website in one minute.")
        }
