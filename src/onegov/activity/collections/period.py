from onegov.activity.models import Period
from onegov.core.collection import GenericCollection


class PeriodCollection(GenericCollection):

    @property
    def model_class(self):
        return Period

    def add(self, title, prebooking, booking, execution, active=False,
            minutes_between=0, deadline_date=None, deadline_days=None,
            cancellation_date=None, cancellation_days=None, finalizable=True,
            confirmable=True):

        if not confirmable:
            prebooking = (booking[0], booking[0])

        period = super().add(
            title=title,
            prebooking_start=prebooking[0],
            prebooking_end=prebooking[1],
            booking_start=booking[0],
            booking_end=booking[1],
            execution_start=execution[0],
            execution_end=execution[1],
            minutes_between=minutes_between,
            active=active,
            deadline_date=deadline_date,
            deadline_days=deadline_days,
            cancellation_date=cancellation_date,
            cancellation_days=cancellation_days,
            finalizable=finalizable,
            confirmable=confirmable,
        )

        if not confirmable:
            period.confirmed = True

        return period

    def active(self):
        return self.query().filter(Period.active == True).first()
