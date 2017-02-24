from onegov.activity.models import Occasion, OccasionDate
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

    def add(self, activity, period, start, end, timezone,
            meeting_point=None, age=None, spots=None, note=None, cost=0,
            exclude_from_overlap_check=False):

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        occasion = super().add(
            meeting_point=meeting_point,
            age=age and self.to_half_open_interval(*age),
            spots=spots and self.to_half_open_interval(*spots),
            note=note,
            activity_id=activity.id,
            period_id=period.id,
            cost=cost,
            exclude_from_overlap_check=exclude_from_overlap_check
        )

        self.add_date(occasion, start, end, timezone)

        return occasion

    def add_date(self, occasion, start, end, timezone):

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        date = OccasionDate(
            start=start,
            end=end,
            timezone=timezone
        )

        occasion.dates.append(date)
        self.session.flush()

        return date

    def find_date(self, occasion, start, end, timezone):
        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.start == start)
        q = q.filter(OccasionDate.end == end)
        q = q.filter(OccasionDate.timezone == timezone)

        return q.first()

    def remove_date(self, date):
        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.id == date.id)

        date = q.first()

        if date:
            self.session.delete(date)

    def clear_dates(self, occasion):
        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.occasion_id == occasion.id)

        for date in q:
            self.session.delete(date)

        occasion.dates = []
        self.session.flush()
