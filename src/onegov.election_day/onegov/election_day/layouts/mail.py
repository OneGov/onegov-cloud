from cached_property import cached_property
from onegov.ballot import Vote
from onegov.core.i18n import SiteLocale
from onegov.election_day import _
from onegov.election_day.layouts.default import DefaultLayout


class MailLayout(DefaultLayout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self):
        return self.app.theme_options.get('primary-color', '#fff')

    def model_title(self, model):
        """ Returns the translated title of the given election or vote. Falls
        back to the title of the default fallback, if no translated title is
        available. """

        return model.get_title(
            self.request.locale,
            self.request.default_locale
        )

    def model_url(self, model):
        """ Returns the localized link to the given election of vote. """

        return self.request.link(
            SiteLocale(self.request.locale, self.request.link(model))
        )

    def subject(self, model):
        """ Returns a nice subject for the given model. """

        result = _("New intermediate results")
        if model.completed:
            result = _("Final results")
            if isinstance(model, Vote):
                if model.answer == 'accepted' or model.answer == 'proposal':
                    result = _("Accepted")
                if model.answer == 'rejected':
                    result = _("Rejected")
                if model.answer == 'counter-proposal':
                    result = _("Counter proposal accepted")

        parts = [self.model_title(model), self.request.translate(result)]
        parts = [part for part in parts if part]
        return ' - '.join(parts)

    @cached_property
    def optout_link(self):
        """ Returns the opt-out link of the principal. """

        return self.request.link(
            self.request.app.principal, 'unsubscribe-email'
        )
