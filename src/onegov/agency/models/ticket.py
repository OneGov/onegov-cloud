from functools import cached_property
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


class AgencyMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'AGN'}  # type:ignore
    es_type_name = 'agency_tickets'

    def reference_group(self, request):
        return self.title


class PersonMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'PER'}  # type:ignore
    es_type_name = 'person_tickets'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('AGN')
class AgencyMutationHandler(Handler):

    handler_title = _("Agency")
    code_title = _("Agencies")

    @cached_property
    def collection(self):
        return ExtendedAgencyCollection(self.session)

    @cached_property
    def agency(self):
        return self.collection.by_id(self.data['handler_data']['id'])

    @cached_property
    def mutation(self):
        if self.agency:
            return AgencyMutation(None, self.agency.id, self.ticket.id)

    @property
    def deleted(self):
        return self.agency is None

    @cached_property
    def email(self):
        return (
            self.data['handler_data'].get('submitter_email', '')
            or self.data['handler_data'].get('email', '')
        )

    @cached_property
    def message(self):
        return (
            self.data['handler_data'].get('submitter_message', '')
            or self.data['handler_data'].get('message', '')
        )

    @cached_property
    def proposed_changes(self):
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self):
        return self.data.get('state')

    @property
    def title(self):
        return self.agency.title

    @property
    def subtitle(self):
        return _("Mutation")

    @cached_property
    def group(self):
        return _("Agency")

    def get_summary(self, request):
        layout = AgencyLayout(self.agency, request)
        return render_macro(
            layout.macros['display_agency_mutation'],
            request,
            {
                'agency': self.agency,
                'message': linkify(self.message).replace('\n', '<br>'),
                'proposed_changes': self.proposed_changes,
                'labels': self.mutation.labels,
                'layout': layout
            }
        )

    def get_links(self, request):
        if self.deleted:
            return []

        links = [
            Link(
                text=_("Edit agency"),
                url=request.return_here(
                    request.link(self.agency.proxy(), 'edit')
                ),
                attrs={'class': 'edit-link'}
            )
        ]

        if self.proposed_changes and self.state is None:
            links.append(
                Link(
                    text=_("Apply proposed changes"),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )

        return links


@handlers.registered_handler('PER')
class PersonMutationHandler(Handler):

    handler_title = _("Person")
    code_title = _("People")

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.session)

    @cached_property
    def person(self):
        return self.collection.by_id(self.data['handler_data']['id'])

    @cached_property
    def mutation(self):
        if self.person:
            return PersonMutation(None, self.person.id, self.ticket.id)

    @property
    def deleted(self):
        return self.person is None

    @cached_property
    def email(self):
        return (
            self.data['handler_data'].get('submitter_email', '')
            or self.data['handler_data'].get('email', '')
        )

    @cached_property
    def message(self):
        return (
            self.data['handler_data'].get('submitter_message', '')
            or self.data['handler_data'].get('message', '')
        )

    @cached_property
    def proposed_changes(self):
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self):
        return self.data.get('state')

    @property
    def title(self):
        return self.person.title

    @property
    def subtitle(self):
        return _("Mutation")

    @cached_property
    def group(self):
        return _("Person")

    def get_summary(self, request):
        layout = ExtendedPersonLayout(self.person, request)
        return render_macro(
            layout.macros['display_person_mutation'],
            request,
            {
                'person': self.person,
                'message': linkify(self.message).replace('\n', '<br>'),
                'proposed_changes': self.proposed_changes,
                'labels': self.mutation.labels,
                'layout': layout
            }
        )

    def get_links(self, request):
        if self.deleted:
            return []

        links = [
            Link(
                text=_("Edit person"),
                url=request.return_here(
                    request.link(self.person, 'edit')
                ),
                attrs={'class': 'edit-link'}
            )
        ]

        if self.proposed_changes and self.state is None:
            links.append(
                Link(
                    text=_("Apply proposed changes"),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )
        return links
