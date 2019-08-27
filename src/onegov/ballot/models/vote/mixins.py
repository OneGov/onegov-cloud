from sqlalchemy import case
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property


class DerivedAttributesMixin(object):

    """ A simple mixin to add commonly used functions to ballots and their
    results. """

    @hybrid_property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @yeas_percentage.expression
    def yeas_percentage(self):
        # coalesce will pick the first non-null result
        # nullif will return null if division by zero
        # => when all yeas and nays are zero the yeas percentage is 0%
        return 100 * (
            self.yeas / (
                func.coalesce(
                    func.nullif(self.yeas + self.nays, 0), 1
                )
            )
        )

    @hybrid_property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @hybrid_property
    def accepted(self):
        return self.yeas > self.nays if self.counted else None

    @accepted.expression
    def accepted(cls):
        return case({True: cls.yeas > cls.nays}, cls.counted)


class DerivedBallotsCountMixin(object):

    """ A simple mixin to add commonly used functions to votes, ballots and
    their results. """

    @hybrid_property
    def cast_ballots(self):
        return self.yeas + self.nays + self.empty + self.invalid

    @hybrid_property
    def turnout(self):
        return self.cast_ballots / self.eligible_voters * 100\
            if self.eligible_voters else 0
