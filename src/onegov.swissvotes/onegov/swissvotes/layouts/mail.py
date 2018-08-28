from cached_property import cached_property
from onegov.swissvotes.layouts.default import DefaultLayout


class MailLayout(DefaultLayout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self):
        return self.app.theme_options.get('primary-color', '#fff')
