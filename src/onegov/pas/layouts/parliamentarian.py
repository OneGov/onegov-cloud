from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.layouts.default import DefaultLayout


class PASParliamentarianCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Parliamentarians')

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


class PASParliamentarianLayout(DefaultLayout):

    @cached_property
    def collection(self) -> PASParliamentarianCollection:
        return PASParliamentarianCollection(self.request.app)

    @cached_property
    def title(self) -> str:
        return f'{self.model.first_name} {self.model.last_name}'

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(
                _('Parliamentarians'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]
