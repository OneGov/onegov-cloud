import morepath

from onegov.onboarding import _
from onegov.onboarding.forms import TownForm, TownSettingsForm
from onegov.onboarding.models.assistant import Assistant


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town onboarding. """

    @Assistant.step(form=TownForm)
    def first_step(self, request, form):

        if form.submitted(request):
            request.browser_session['name'] = form.data['name']
            request.browser_session['user'] = form.data['user']

            return morepath.redirect(request.link(self.for_next_step()))

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }

    @Assistant.step(form=TownSettingsForm)
    def second_step(self, request, form):

        for key in ('name', 'user'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_prev_step()))

        if form.submitted(request):
            request.browser_session['color'] = form.data['color'].get_hex()

            return morepath.redirect(request.link(self.for_next_step()))

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }

    @Assistant.step(form=None)
    def last_step(self, request):

        for key in ('name', 'user', 'color'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_first_step()))

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }
