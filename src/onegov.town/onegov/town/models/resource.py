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
from onegov.town import utils
from uuid import uuid5


class SharedMethods(object):

    lead = meta_property('lead')
    text = content_property('text')

    @property
    def deletable(self):
        if self.scheduler.managed_reserved_slots().first():
            return False

        if self.scheduler.managed_reservations().first():
            return False

        return True

    def remove_expired_reservation_sessions(self, expiration_date=None):
        session = self.libres_context.get_service('session_provider').session()
        queries = self.scheduler.queries

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

    def request_bound_reservations(self, request, status='pending'):
        """ Returns the reservations associated with this resource and the
        current user.

        """

        session = utils.get_libres_session_id(request)
        scheduler = self.get_scheduler(request.app.libres_context)

        res = scheduler.queries.reservations_by_session(session)
        res = res.filter(Reservation.resource == self.id)
        res = res.filter(Reservation.status == status)
        res = res.order_by(False)  # clear existing order
        res = res.order_by(Reservation.start)

        return res

    def request_bound_submission_id(self, request):
        """ Returns the submission id for request and the current resouce. """
        session = utils.get_libres_session_id(request)

        return uuid5(self.id, session.hex)


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
