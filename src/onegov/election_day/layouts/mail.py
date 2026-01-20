from __future__ import annotations

from functools import cached_property
from onegov.core.i18n import SiteLocale
from onegov.election_day import _
from onegov.election_day.layouts.default import DefaultLayout
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import PageTemplateFile
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompound


class MailLayout(DefaultLayout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self) -> PageTemplateFile:
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self) -> str:
        return self.app.theme_options.get('primary-color', '#fff')

    def model_title(
        self,
        model: Election | ElectionCompound | Vote
    ) -> str | None:
        """ Returns the translated title of the given election or vote. Falls
        back to the title of the default fallback, if no translated title is
        available. """

        assert self.request.locale
        return model.get_title(
            self.request.locale,
            self.request.default_locale
        )

    def model_url(self, model: object) -> str:
        """ Returns the localized link to the given election of vote. """

        assert self.request.locale
        return SiteLocale(self.request.locale).link(
            self.request, self.request.link(model)
        )

    def subject(self, model: Election | ElectionCompound | Vote) -> str:
        """ Returns a nice subject for the given model. """

        result = _('New intermediate results')
        if model.completed:
            result = _('Final results')
            if isinstance(model, Vote):
                if model.answer == 'accepted' or model.answer == 'proposal':
                    result = _('Accepted')
                if model.answer == 'rejected':
                    result = _('Rejected')
                if model.answer == 'counter-proposal':
                    if model.direct:
                        result = _('Direct counter proposal accepted')
                    else:
                        result = _('Indirect counter proposal accepted')

        parts = (self.model_title(model), self.request.translate(result))
        return ' - '.join(part for part in parts if part)

    @cached_property
    def optout_link(self) -> str:
        """ Returns the opt-out link of the principal. """

        return self.request.link(
            self.request.app.principal, 'unsubscribe-email'
        )
