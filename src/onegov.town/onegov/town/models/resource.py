from libres.db.models import Reservation
from onegov.core.orm.mixins import meta_property, content_property
from onegov.libres.models import Resource
from onegov.form.models import FormSubmission
from onegov.town.models.extensions import (
    HiddenFromPublicExtension,
    ContactExtension,
    PersonLinkExtension,
    CoordinatesExtension
)
from onegov.search import ORMSearchable


class SharedMethods(object):

    lead = meta_property('lead')
    text = content_property('text')

    def deletable(self, libres_context):
        scheduler = self.get_scheduler(libres_context)

        if scheduler.managed_reserved_slots().first():
            return False

        if scheduler.managed_reservations().first():
            return False

        return True

    def remove_expired_reservation_sessions(self, libres_context,
                                            expiration_date=None):
        session = libres_context.get_service('session_provider').session()
        queries = self.get_scheduler(libres_context).queries

        expired_sessions = queries.find_expired_reservation_sessions(
            expiration_date)

        if expired_sessions:
            query = session.query(Reservation).with_entities(Reservation.token)
            query = query.filter(Reservation.session_id.in_(expired_sessions))
            tokens = set(r[0] for r in query.all())

            query = session.query(FormSubmission)
            query = query.filter(FormSubmission.name == None)
            query = query.filter(FormSubmission.id.in_(tokens))

            query.delete('fetch')
            queries.remove_expired_reservation_sessions(expiration_date)


class SearchableResource(ORMSearchable):

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'}
    }

    @property
    def es_language(self):
        return 'de'  # XXX add to database in the future

    @property
    def es_public(self):
        return not self.is_hidden_from_public


class DaypassResource(Resource, HiddenFromPublicExtension, SearchableResource,
                      ContactExtension, PersonLinkExtension,
                      CoordinatesExtension, SharedMethods):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}

    es_type_name = 'daypasses'


class RoomResource(Resource, HiddenFromPublicExtension, SearchableResource,
                   ContactExtension, PersonLinkExtension,
                   CoordinatesExtension, SharedMethods):
    __mapper_args__ = {'polymorphic_identity': 'room'}

    es_type_name = 'rooms'
