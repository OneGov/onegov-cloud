from libres.db.models import Reservation
from onegov.core.orm import ModelBase


class PayableReservation(Reservation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'payable'}
