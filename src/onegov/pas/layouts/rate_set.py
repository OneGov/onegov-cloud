from __future__ import annotations

from decimal import Decimal
from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import RateSetCollection
from onegov.pas.layouts.default import DefaultLayout


class RateSetCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Rate sets')

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
                            text=_('Rate set'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-rate-set'}
                        ),
                    ]
                ),
            ]
        return None


class RateSetLayout(DefaultLayout):

    @cached_property
    def collection(self) -> RateSetCollection:
        return RateSetCollection(self.request.session)

    def format_rate(self, amount: float | int | Decimal) -> str:
        value = Decimal(str(amount))
        if value == value.to_integral_value():
            return f'CHF {int(value)}.-'
        return f'CHF {value:.2f}'

    @cached_property
    def title(self) -> str:
        return '{} {}'.format(
            self.request.translate(_('Rate set')),
            self.model.year
        )

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(
                _('Rate sets'),
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
                            _('Do you really want to delete this rate set?'),
                            _('This cannot be undone.'),
                            _('Delete rate set'),
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
