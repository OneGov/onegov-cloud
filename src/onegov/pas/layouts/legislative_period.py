from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.layouts.default import DefaultLayout


class LegislativePeriodCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Legislative periods')

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
                            text=_('Legislative period'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-legislative-period'}
                        ),
                    ]
                ),
            ]
        return None


class LegislativePeriodLayout(DefaultLayout):

    @cached_property
    def collection(self) -> LegislativePeriodCollection:
        return LegislativePeriodCollection(self.request.session)

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
                _('Legislative periods'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link] | None:
        if self.request.is_manager:
            return [
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
                                'legislative period?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete legislative period'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.collection
                            )
                        )
                    )
                )
            ]
        return None
