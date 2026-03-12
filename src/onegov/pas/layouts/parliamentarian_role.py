from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
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
                    text=_('Remove'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to remove this role?'),
                            _('This cannot be undone.'),
                            _('Remove role'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.model.parliamentarian
                            )
                        )
                    )
                )
            ]
        return None
