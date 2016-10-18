from onegov.activity.models import Period
from onegov.core.collection import GenericCollection
from sedate import standardize_date


class PeriodCollection(GenericCollection):

    @property
    def model_class(self):
        return Period

    def add(self, title, prebooking, execution, timezone, active=False):

        prebooking_start = standardize_date(prebooking[0], timezone)
        prebooking_end = standardize_date(prebooking[1], timezone)

        execution_start = standardize_date(execution[0], timezone)
        execution_end = standardize_date(execution[1], timezone)

        return super().add(
            title=title,
            prebooking_start=prebooking_start,
            prebooking_end=prebooking_end,
            execution_start=execution_start,
            execution_end=execution_end,
            active=active,
            timezone=timezone
        )

    def active(self):
        return self.query().filter(Period.active == True).first()
