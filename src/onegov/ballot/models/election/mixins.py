from collections import OrderedDict
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


class PartyResultExportMixin:

    """ A mixin allowing to export the party results optionally including the
    panachage data.

    Panachage data with an empty source is assumed to represent the votes from
    the blank list and exported with ID '999'.

    """

    def export_parties(self, locales, default_locale, json_serializable=False):
        """ Returns all party results with the panachage as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        If `json_serializable` is True, decimals are converted to floats. This
        might be a lossy conversation!

        """

        def convert_decimal(value):
            if value is None:
                return value
            if json_serializable:
                return float(value)
            return str(value)

        results = {}

        # get the party results
        for result in self.party_results:
            year = results.setdefault(result.year, {})
            year[result.party_id] = {
                'name_translations': result.name_translations,
                'total_votes': result.total_votes,
                'color': result.color,
                'mandates': result.number_of_mandates,
                'votes': result.votes,
                'voters_count': result.voters_count,
                'voters_count_percentage': result.voters_count_percentage
            }

        # get the panachage results
        for result in self.panachage_results:
            year = results.setdefault(self.date.year, {})
            target = year.setdefault(result.target, {})
            target[result.source] = result.votes

        rows = []
        parties = sorted({key for r in results.values() for key in r.keys()})
        for year in sorted(results.keys(), reverse=True):
            for party_id in parties:
                result = results[year].get(party_id, {})

                # add the party results
                row = OrderedDict()
                row['year'] = year
                row['id'] = party_id
                row['name'] = result['name_translations'].get(
                    default_locale, None
                )
                for locale in locales:
                    row[f'name_{locale}'] = result['name_translations'].get(
                        locale, None
                    )
                row['total_votes'] = result['total_votes']
                row['color'] = result['color']
                row['mandates'] = result['mandates']
                row['votes'] = result['votes']
                row['voters_count'] = convert_decimal(result['voters_count'])
                row['voters_count_percentage'] = convert_decimal(
                    result['voters_count_percentage']
                )

                # add the panachage results
                if self.panachage_results.count():
                    for source in parties:
                        column = f'panachage_votes_from_{source}'
                        row[column] = result.get(source, None)
                    row['panachage_votes_from_999'] = result.get('', None)

                rows.append(row)

        return rows
