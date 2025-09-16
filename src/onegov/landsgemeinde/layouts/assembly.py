from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.layouts.default import DefaultLayout


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.landsgemeinde.models import Assembly
    from onegov.landsgemeinde.request import LandsgemeindeRequest


class AssemblyCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Archive')

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
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Assembly'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                ),
            ]
        return None


class AssemblyLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: Assembly

        def __init__(
            self,
            model: Assembly,
            request: LandsgemeindeRequest
        ) -> None: ...

    @cached_property
    def title(self) -> str:
        return self.assembly_title(self.model)

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                self.assembly_type_plural,
                self.request.link(self.assembly_collection())
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            items = AgendaItemCollection(self.app.session(), self.model.date)
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('States'),
                    url=self.request.link(self.model, 'states'),
                    attrs={'class': 'check-list-link'}
                ),
                Link(
                    text=_('Ticker'),
                    url=self.request.link(self.model, 'ticker'),
                    attrs={'class': 'news-link', 'target': '_blank'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this assembly?'),
                            _('This cannot be undone.'),
                            _('Delete assembly'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.assembly_collection()
                            )
                        )
                    )
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Agenda item'),
                            url=self.request.link(items, 'new'),
                            attrs={'class': 'check-list-link'}
                        ),
                        Link(
                            text=_('ZIP Upload'),
                            url=self.request.link(items, 'new-import'),
                            attrs={'class': 'ticket-archive'}
                        ),
                    ]
                )
            ]
        return None


class AssemblyTickerLayout(DefaultLayout):

    model: Assembly

    def __init__(
        self,
        model: Assembly,
        request: LandsgemeindeRequest
    ) -> None:

        super().__init__(model, request)
        self.request.include('websockets')
        self.request.include('ticker')

        self.custom_body_attributes['data-websocket-endpoint'] = (
            self.app.websockets_client_url(request))
        self.custom_body_attributes['data-websocket-schema'] = (
            self.app.schema)

    @cached_property
    def title(self) -> str:
        return self.assembly_title(self.model)

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Ticker'), self.request.link(self.model, name='ticker'))
        ]

    def current_assembly(self) -> None:
        # This way the lifeticker bar won't be displayed
        return None
