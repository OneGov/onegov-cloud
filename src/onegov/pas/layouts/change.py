from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import ChangeCollection
from onegov.pas.layouts.default import DefaultLayout


class ChangeCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Changes')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]


class ChangeLayout(DefaultLayout):

    @cached_property
    def collection(self) -> ChangeCollection:
        return ChangeCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.action_label

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Changes'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]
