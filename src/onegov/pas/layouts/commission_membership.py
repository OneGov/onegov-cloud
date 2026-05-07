from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.layouts.default import DefaultLayout


class PASCommissionMembershipLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.parliamentarian.title

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def commission_collection(self) -> PASCommissionCollection:
        return PASCommissionCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('PAS settings'), self.pas_settings_url),
            Link(
                _('Commissions'),
                self.request.link(self.commission_collection)
            ),
            Link(
                self.model.commission.title,
                self.request.link(self.model.commission)
            ),
            Link(self.title, self.request.link(self.model))
        ]
