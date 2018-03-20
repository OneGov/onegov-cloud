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
        include_panachage = hasattr(self, 'panachage_results')

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
        if include_panachage:
            for result in self.panachage_results:
                year = results.setdefault(self.date.year, {})
                target = year.setdefault(result.target, {})
                target[result.source] = result.votes
                parties |= set([result.source, result.target])

        parties = sorted(parties)

        rows = []
        for year in sorted(results.keys(), reverse=True):
            for party in sorted(results[year].keys()):
                result = results[year][party]

                row = OrderedDict()
                row['year'] = year
                row['name'] = party
                row['id'] = parties.index(party)
                row['total_votes'] = result.get('total_votes', '')
                row['color'] = result.get('color', '')
                row['mandates'] = result.get('mandates', '')
                row['votes'] = result.get('votes', '')

                if include_panachage:
                    for source in parties:
                        column = 'panachage_votes_from_{}'.format(
                            parties.index(source)
                        )
                        row[column] = results[year][party].get(source, '')
                rows.append(row)

        return rows
