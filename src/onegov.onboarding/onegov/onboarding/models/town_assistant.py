from onegov.onboarding import _
from onegov.onboarding.models.assistant import Assistant


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town onboarding. """

    @Assistant.step
    def first_step(self, request):
        return {
            'title': _("The Online Counter for Towns."),
            'bullets': (
                _("Start using the online counter for your town now."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }
