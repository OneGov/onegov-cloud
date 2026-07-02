from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections.parliamentary_group import (
    PASParliamentaryGroupCollection
)
from onegov.pas.layouts.default import DefaultLayout


class PASParliamentaryGroupCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Parliamentary groups')

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


class PASParliamentaryGroupLayout(DefaultLayout):

    @cached_property
    def collection(self) -> PASParliamentaryGroupCollection:
        return PASParliamentaryGroupCollection(self.request.session)

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
                _('Parliamentary groups'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]
