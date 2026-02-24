from __future__ import annotations

from functools import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import PageTemplateFile
    from onegov.core.request import CoreRequest
    from onegov.core.templates import MacrosLookup


class Layout(ChameleonLayout):

    def __init__(self, model: Any, request: CoreRequest):
        super().__init__(model=model, request=request)
        self.request.include('common')

    @cached_property
    def font_awesome_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    @cached_property
    def logo_path(self) -> str:
        static_file = StaticFile.from_application(self.app, 'logo.svg')

        return self.request.link(static_file)

    @cached_property
    def town_names_path(self) -> str:
        static_file = StaticFile.from_application(self.app, 'towns.json')
        return self.request.link(static_file)


class DefaultLayout(Layout):
    pass


class MailLayout(Layout):

    @cached_property
    def base(self) -> PageTemplateFile:
        return self.template_loader['mail_layout.pt']

    @cached_property
    def macros(self) -> MacrosLookup:
        raise NotImplementedError
