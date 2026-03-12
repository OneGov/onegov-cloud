from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
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

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Parliamentarian'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-parliamentarian'},
                        ),
                    ],
                ),
            ]
        return None


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

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Role (as a party or group member)'),
                            url=self.request.link(self.model, 'new-role'),
                            attrs={'class': 'new-role'}
                        ),
                    ]
                ),
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this '
                                'parliamentarian?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete parliamentarian'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.collection
                            )
                        )
                    )
                ),
            ]
        return None
