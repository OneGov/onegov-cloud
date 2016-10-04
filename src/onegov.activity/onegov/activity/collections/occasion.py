from onegov.activity.models import Occasion
from onegov.core.collection import GenericCollection
from psycopg2.extras import NumericRange
from sedate import standardize_date


class OccasionCollection(GenericCollection):

    @property
    def model_class(self):
        return Occasion

    def add(self, activity, start, end, timezone, location,
            age=None, spots=None, note=None):

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        # postgres coerces ranges internally to be half-open in an effort
        # to canonize these ranges - to be consistent we do the same here
        # -> the ranges we take are are closed intervals
        def to_half_open_interval(lower, upper):
            return NumericRange(lower, upper + 1, bounds='[)')

        return super().add(
            start=start,
            end=end,
            timezone=timezone,
            location=location,
            age=age and to_half_open_interval(*age),
            spots=spots and to_half_open_interval(*spots),
            note=note,
            activity_id=activity.id
        )
