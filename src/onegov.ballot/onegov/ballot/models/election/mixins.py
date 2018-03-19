from collections import OrderedDict
from onegov.ballot.models.election.party_result import PartyResult
from sqlalchemy.ext.hybrid import hybrid_property


class DerivedAttributesMixin(object):

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

        return self.received_ballots / self.eligible_voters * 100


class PartyResultsExportMixin(object):

    """ Adds a function to export the party results. """

    def export_parties(self):
        """ Returns all party results as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        results = self.party_results.order_by(
            PartyResult.year.desc(),
            PartyResult.name
        )

        rows = []
        for result in results:
            row = OrderedDict()
            row['year'] = result.year
            row['total_votes'] = result.total_votes
            row['name'] = result.name
            row['color'] = result.color
            row['mandates'] = result.number_of_mandates
            row['votes'] = result.votes
            rows.append(row)

        return rows
