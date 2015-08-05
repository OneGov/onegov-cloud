from onegov.libres.models import Resource
from onegov.town.models.extensions import (
    HiddenFromPublicExtension,
    ContactExtension,
    PersonLinkExtension
)


class DeletableMixin(object):

    def deletable(self, libres_context):
        scheduler = self.get_scheduler(libres_context)

        if scheduler.managed_reserved_slots().first():
            return False

        if scheduler.managed_reservations().first():
            return False

        return True


class DaypassResource(Resource, HiddenFromPublicExtension,
                      ContactExtension, PersonLinkExtension, DeletableMixin):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}


class RoomResource(Resource, HiddenFromPublicExtension,
                   ContactExtension, PersonLinkExtension, DeletableMixin):
    __mapper_args__ = {'polymorphic_identity': 'room'}
