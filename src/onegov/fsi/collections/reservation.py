from onegov.core.collection import GenericCollection


class ReservationCollection(GenericCollection):

    @property
    def model_class(self):
        from onegov.fsi.models.reservation import Reservation
        return Reservation