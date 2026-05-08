from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.layouts.default import DefaultLayout


class PresidentialAllowanceCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Presidential allowances')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('PAS settings'), self.pas_settings_url
            ),
            Link(
                self.title,
                self.request.link(self.model),
            ),
        ]

    @cached_property
    def editbar_links(
        self,
    ) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Add allowance'),
                            url=self.request.link(
                                self.model, 'new'
                            ),
                            attrs={
                                'class': (
                                    'new-presidential-allowance'
                                )
                            },
                        ),
                    ],
                ),
            ]
        return None


class PresidentialAllowanceFormLayout(DefaultLayout):

    @cached_property
    def collection(
        self,
    ) -> PresidentialAllowanceCollection:
        return PresidentialAllowanceCollection(
            self.request.session
        )

    @cached_property
    def title(self) -> str:
        return _('Add allowance')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('PAS settings'), self.pas_settings_url
            ),
            Link(
                _('Presidential allowances'),
                self.request.link(self.collection),
            ),
            Link(
                self.title,
                self.request.link(self.model, 'new'),
            ),
        ]
