from __future__ import annotations

from functools import cached_property
from markupsafe import Markup
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.layout import AgencyLayout
from onegov.agency.layout import ExtendedPersonLayout
from onegov.agency.models import AgencyMutation
from onegov.agency.models import PersonMutation
from onegov.core.elements import Link
from onegov.core.templates import render_macro
from onegov.core.utils import linkify
from onegov.org import _
from onegov.org.models.ticket import OrgTicketMixin
from onegov.ticket import Handler
from onegov.ticket import handlers
from onegov.ticket import Ticket


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedPerson
    from onegov.org.request import OrgRequest


class AgencyMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'AGN'}

    if TYPE_CHECKING:
        @property
        def handler(self) -> AgencyMutationHandler: ...

    def reference_group(self, request: OrgRequest) -> str:
        return self.title


class PersonMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'PER'}

    if TYPE_CHECKING:
        @property
        def handler(self) -> PersonMutationHandler: ...

    def reference_group(self, request: OrgRequest) -> str:
        return self.title


@handlers.registered_handler('AGN')
class AgencyMutationHandler(Handler):

    handler_title = _('Agency')
    code_title = _('Agencies')

    @cached_property
    def collection(self) -> ExtendedAgencyCollection:
        return ExtendedAgencyCollection(self.session)

    @cached_property
    def agency(self) -> ExtendedAgency | None:
        return self.collection.by_id(self.data['handler_data']['id'])

    @cached_property
    def mutation(self) -> AgencyMutation | None:
        if self.agency:
            return AgencyMutation(self.session, self.agency.id, self.ticket.id)
        return None

    @property
    def deleted(self) -> bool:
        return self.agency is None

    @cached_property
    def email(self) -> str:
        return (
            self.data['handler_data'].get('submitter_email', '')
            or self.data['handler_data'].get('email', '')
        )

    @cached_property
    def message(self) -> str:
        return (
            self.data['handler_data'].get('submitter_message', '')
            or self.data['handler_data'].get('message', '')
        )

    @cached_property
    def proposed_changes(self) -> dict[str, Any]:
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self) -> str | None:
        return self.data.get('state')

    @property
    def title(self) -> str:
        return self.agency.title if self.agency else '<deleted>'

    @property
    def subtitle(self) -> str:
        return _('Mutation')

    @cached_property
    def group(self) -> str:
        return _('Agency')

    def get_summary(
        self,
        request: AgencyRequest  # type:ignore[override]
    ) -> Markup:

        layout = AgencyLayout(self.agency, request)
        return render_macro(
            layout.macros['display_agency_mutation'],
            request,
            {
                'agency': self.agency,
                'message': linkify(self.message).replace('\n', Markup('<br>')),
                'proposed_changes': self.proposed_changes,
                'labels': self.mutation.labels if self.mutation else {},
                'layout': layout
            }
        )

    def get_links(self, request: AgencyRequest) -> list[Link]:  # type:ignore
        if self.deleted:
            return []

        assert self.agency is not None
        links = [
            Link(
                text=_('Edit agency'),
                url=request.return_here(
                    request.link(self.agency.proxy(), 'edit')
                ),
                attrs={'class': 'edit-link'}
            )
        ]

        if self.proposed_changes and self.state is None:
            assert self.mutation is not None
            links.append(
                Link(
                    text=_('Apply proposed changes'),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )

        return links


@handlers.registered_handler('PER')
class PersonMutationHandler(Handler):

    handler_title = _('Person')
    code_title = _('People')

    @cached_property
    def collection(self) -> ExtendedPersonCollection:
        return ExtendedPersonCollection(self.session)

    @cached_property
    def person(self) -> ExtendedPerson | None:
        return self.collection.by_id(self.data['handler_data']['id'])

    @cached_property
    def mutation(self) -> PersonMutation | None:
        if self.person:
            return PersonMutation(self.session, self.person.id, self.ticket.id)
        return None

    @property
    def deleted(self) -> bool:
        return self.person is None

    @cached_property
    def email(self) -> str:
        return (
            self.data['handler_data'].get('submitter_email', '')
            or self.data['handler_data'].get('email', '')
        )

    @cached_property
    def message(self) -> str:
        return (
            self.data['handler_data'].get('submitter_message', '')
            or self.data['handler_data'].get('message', '')
        )

    @cached_property
    def proposed_changes(self) -> dict[str, Any]:
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self) -> str | None:
        return self.data.get('state')

    @property
    def title(self) -> str:
        return self.person.title if self.person else '<deleted>'

    @property
    def subtitle(self) -> str:
        return _('Mutation')

    @cached_property
    def group(self) -> str:
        return _('Person')

    def get_summary(
        self,
        request: AgencyRequest  # type:ignore[override]
    ) -> Markup:

        layout = ExtendedPersonLayout(self.person, request)
        return render_macro(
            layout.macros['display_person_mutation'],
            request,
            {
                'person': self.person,
                'message': linkify(self.message).replace('\n', Markup('<br>')),
                'proposed_changes': self.proposed_changes,
                'labels': self.mutation.labels if self.mutation else {},
                'layout': layout
            }
        )

    def get_links(self, request: AgencyRequest) -> list[Link]:  # type:ignore
        if self.deleted:
            return []

        assert self.person is not None
        links = [
            Link(
                text=_('Edit person'),
                url=request.return_here(
                    request.link(self.person, 'edit')
                ),
                attrs={'class': 'edit-link'}
            )
        ]

        if self.proposed_changes and self.state is None:
            assert self.mutation is not None
            links.append(
                Link(
                    text=_('Apply proposed changes'),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )
        return links
