from libres.db.models import Reservation
from onegov.libres.models import Resource
from onegov.form.models import FormSubmission
from onegov.town.models.extensions import (
    HiddenFromPublicExtension,
    ContactExtension,
    PersonLinkExtension
)


class SharedMethods(object):

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
        scheduler = self.get_scheduler(libres_context)

        find = scheduler.queries.find_expired_reservation_sessions
        remove = scheduler.queries.remove_expired_reservation_sessions

        expired_sessions = find(expiration_date)

        query = session.query(Reservation).with_entities(Reservation.token)
        query = query.filter(Reservation.session_id.in_(expired_sessions))
        tokens = set(r[0] for r in query.all())

        remove(expiration_date)

        query = session.query(FormSubmission)
        query = query.filter(FormSubmission.name == None)
        query = query.filter(FormSubmission.id.in_(tokens))

        query.delete('fetch')


class DaypassResource(Resource, HiddenFromPublicExtension,
                      ContactExtension, PersonLinkExtension, SharedMethods):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}


class RoomResource(Resource, HiddenFromPublicExtension,
                   ContactExtension, PersonLinkExtension, SharedMethods):
    __mapper_args__ = {'polymorphic_identity': 'room'}
