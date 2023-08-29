from functools import cached_property
from onegov.wtfs.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import BaseTemplate


class MailLayout(DefaultLayout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self) -> 'BaseTemplate':
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self) -> str:
        return self.app.theme_options.get('primary-color', '#fff')
