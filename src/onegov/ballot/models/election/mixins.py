from sqlalchemy.ext.hybrid import hybrid_property


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to elections and their
    results. """

    @hybrid_property
    def unaccounted_ballots(self):
        """ The number of unaccounted ballots. """

        return self.blank_ballots + self.invalid_ballots

    @hybrid_property
    def accounted_ballots(self):
        """ The number of accounted ballots. """

        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property
    def turnout(self):
        """ The turnout of the election. """

        if not self.eligible_voters:
            return 0

        if not self.counted_eligible_voters:
            return 0

        return self.counted_received_ballots /\
            self.counted_eligible_voters * 100
