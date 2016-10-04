from onegov.activity.models import Occasion
from onegov.core.collection import GenericCollection
from psycopg2.extras import NumericRange
from sedate import standardize_date


class OccasionCollection(GenericCollection):

    @property
    def model_class(self):
        return Occasion

    @staticmethod
    def to_half_open_interval(lower, upper):
        """ Postgres coerces ranges internally to be half-open in an effort
        to canonize these ranges. This function does the same by taking
        a closed interval and turning it into a half-open interval of
        the NumericRange type.

        """
        return NumericRange(lower, upper + 1, bounds='[)')

    def add(self, activity, start, end, timezone,
            location=None, age=None, spots=None, note=None):

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        return super().add(
            start=start,
            end=end,
            timezone=timezone,
            location=location,
            age=age and self.to_half_open_interval(*age),
            spots=spots and self.to_half_open_interval(*spots),
            note=note,
            activity_id=activity.id
        )
