from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.layouts.default import DefaultLayout


class PASParliamentarianRoleLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.role_label

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def parliamentarian_collection(self) -> PASParliamentarianCollection:
        return PASParliamentarianCollection(self.request.app)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(
                _('Parliamentarians'),
                self.request.link(self.parliamentarian_collection)
            ),
            Link(
                self.model.parliamentarian.title,
                self.request.link(self.model.parliamentarian)
            ),
            Link(self.title, self.request.link(self.model))
        ]
