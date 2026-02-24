from __future__ import annotations

from functools import cached_property
from onegov.swissvotes.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import PageTemplateFile


class MailLayout(DefaultLayout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self) -> PageTemplateFile:
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self) -> str:
        return self.app.theme_options.get('primary-color', '#fff')
