from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import AttendenceCollection
from onegov.pas.layouts.default import DefaultLayout


class AttendenceCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Attendences')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
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
                            text=_('New Attendence'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-attendence'}
                        ),
                        Link(
                            text=_('Plenary session (bulk)'),
                            url=self.request.link(self.model, 'new-bulk'),
                            attrs={'class': 'new-attendence'}
                        ),
                        Link(
                            text=_('Commission session (bulk)'),
                            url=self.request.link(
                                self.model, 'new-commission-bulk'
                            ),
                            attrs={'class': 'new-attendence'},
                        ),
                    ]
                ),
            ]
        return None


class AttendenceLayout(DefaultLayout):

    @cached_property
    def collection(self) -> AttendenceCollection:
        return AttendenceCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.type_label

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Attendences'),
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
                            _('Do you really want to delete this meeting?'),
                            _('This cannot be undone.'),
                            _('Delete meeting'),
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
