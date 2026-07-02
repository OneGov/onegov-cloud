from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import PartyCollection
from onegov.pas.layouts.default import DefaultLayout


class PartyCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Parties')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(self.title, self.request.link(self.model))
        ]


class PartyLayout(DefaultLayout):

    @cached_property
    def collection(self) -> PartyCollection:
        return PartyCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.name

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(
                _('Parties'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]
