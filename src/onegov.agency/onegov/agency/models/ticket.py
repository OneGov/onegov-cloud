from cached_property import cached_property
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.layouts import AgencyLayout
from onegov.agency.layouts import ExtendedPersonLayout
from onegov.core.templates import render_macro
from onegov.org import _
from onegov.org.models.ticket import OrgTicketMixin
from onegov.ticket import Handler
from onegov.ticket import handlers
from onegov.ticket import Ticket


class AgencyMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'AGN'}
    es_type_name = 'agency_tickets'

    def reference_group(self, request):
        return self.title


class PersonMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'PER'}
    es_type_name = 'person_tickets'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('AGN')
class AgencyMutationHandler(Handler):

    handler_title = _("Agency")

    @cached_property
    def collection(self):
        return ExtendedAgencyCollection(self.session)

    @cached_property
    def agency(self):
        return self.collection.by_id(self.data['handler_data']['id'])

    @property
    def deleted(self):
        return self.agency is None

    @cached_property
    def email(self):
        return self.data['handler_data']['submitter_email']

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
                'message': self.data['handler_data']['submitter_message'],
                'layout': layout
            }
        )

    def get_links(self, request):
        return []


@handlers.registered_handler('PER')
class PersonMutationHandler(Handler):

    handler_title = _("Person")

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.session)

    @cached_property
    def person(self):
        return self.collection.by_id(self.data['handler_data']['id'])

    @property
    def deleted(self):
        return self.person is None

    @cached_property
    def email(self):
        return self.data['handler_data']['submitter_email']

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
                'message': self.data['handler_data']['submitter_message'],
                'layout': layout
            }
        )

    def get_links(self, request):
        return []
