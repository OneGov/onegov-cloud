from collections import OrderedDict
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


class PartyResultExportMixin(object):

    """ A mixin allowing to export the party results optionally including the
    panachage data.

    Panachage data with an empty source is assumed to represent the votes from
    the blank list and exported with ID '999'.

    """

    def export_parties(self):
        """ Returns all party results with the panachage as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        results = {}
        parties = set()

        # get the party results
        for result in self.party_results:
            year = results.setdefault(result.year, {})
            year[result.name] = {
                'total_votes': result.total_votes,
                'color': result.color,
                'mandates': result.number_of_mandates,
                'votes': result.votes
            }
            parties |= set([result.name])

        # get the panachage results
        for result in self.panachage_results:
            year = results.setdefault(self.date.year, {})
            target = year.setdefault(result.target, {})
            target[result.source] = result.votes
            parties |= set([result.source, result.target])

        parties = sorted([party for party in parties if party])

        rows = []
        for year in sorted(results.keys(), reverse=True):
            for party in parties:
                result = results[year].get(party, {})

                # add the party results
                row = OrderedDict()
                row['year'] = year
                row['name'] = party
                row['id'] = parties.index(party)
                row['total_votes'] = result.get('total_votes', '')
                row['color'] = result.get('color', '')
                row['mandates'] = result.get('mandates', '')
                row['votes'] = result.get('votes', '')

                # add the panachage results
                for source in parties:
                    id_ = parties.index(source)
                    column = 'panachage_votes_from_{}'.format(id_)
                    row[column] = result.get(source, '')
                row['panachage_votes_from_999'] = result.get('', '')
                rows.append(row)

        return rows
