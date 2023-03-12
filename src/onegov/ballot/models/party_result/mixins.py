from collections import OrderedDict
from onegov.ballot.models.party_result.party_result import PartyResult
from onegov.core.orm.mixins import meta_property
from sqlalchemy import or_


class PartyResultsOptionsMixin:

    #: Display voters counts instead of votes in views.
    voters_counts = meta_property(default=False)

    #: Display exact voters counts instead of rounded values.
    exact_voters_counts = meta_property(default=False)

    #: may be used to enable/disable the visibility of party strengths
    show_party_strengths = meta_property(default=False)

    #: show a horizontal party strengths bar chart instead of a vertical
    horizontal_party_strengths = meta_property(default=False)

    #: may be used to enable/disable the visibility of party panachage
    show_party_panachage = meta_property(default=False)

    #: may be used to enable/disable the visibility of the seat allocation
    show_seat_allocation = meta_property(default=False)

    #: may be used to enable/disable the visibility of the list groups
    show_list_groups = meta_property(default=False)

    #: may be used to enable fetching party results from previous elections
    use_historical_party_results = meta_property(default=False)


class PartyResultsCheckMixin:

    @property
    def has_party_results(self):
        return self.party_results.filter(
            or_(
                PartyResult.votes > 0,
                PartyResult.voters_count > 0,
                PartyResult.number_of_mandates > 0
            )
        ).first() is not None

    @property
    def has_party_panachage_results(self):
        return self.party_panachage_results.first() is not None


class HistoricalPartyResultsMixin:

    @property
    def relationships_for_historical_party_results(self):
        raise NotImplementedError()

    @property
    def historical_party_results(self):
        """ Returns the party results while adding party results from the last
        legislative period, Requires that a related election or compound has
        been set with type "historical".

        """

        relationships = self.relationships_for_historical_party_results
        relationships = relationships.filter_by(type='historical').all()
        if not relationships:
            return self.party_results
        target = sorted(
            (
                related.target for related in relationships
                if related.target.date < self.date
            ),
            key=lambda related: related.date,
            reverse=True
        )
        if not target:
            return self.party_results

        return self.party_results.union(
            target[0].party_results.filter_by(year=target[0].date.year)
        )

    @property
    def historical_colors(self):
        result = getattr(self, 'colors', {}).copy()
        if not result:
            return result
        relationships = self.relationships_for_historical_party_results
        relationships = relationships.filter_by(type='historical')
        for relation in relationships:
            for key, value in getattr(relation.target, 'colors', {}).items():
                result.setdefault(key, value)
        return result


class PartyResultsExportMixin:

    """  A mixin adding historical party resulta and allowing to export the
    party results optionally including the panachage data.

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

        result = []
        parts = {(r.domain, r.domain_segment) for r in self.party_results}
        for domain, domain_segment in sorted(parts):
            result.extend(
                self._export_parties(
                    locales, default_locale,
                    json_serializable,
                    domain, domain_segment
                )
            )
        return result

    def _export_parties(self, locales, default_locale, json_serializable=False,
                        domain=None, domain_segment=None):
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
            if result.domain != (domain or self.domain):
                continue
            if domain_segment and result.domain_segment != domain_segment:
                continue
            year = results.setdefault(result.year, {})
            year[result.party_id] = {
                'domain': result.domain,
                'domain_segment': result.domain_segment,
                'name_translations': result.name_translations,
                'total_votes': result.total_votes,
                'mandates': result.number_of_mandates,
                'votes': result.votes,
                'voters_count': result.voters_count,
                'voters_count_percentage': result.voters_count_percentage
            }

        # get the panachage results
        if domain == self.domain:
            for result in self.party_panachage_results:
                year = results.setdefault(self.date.year, {})
                target = year.setdefault(result.target, {})
                target[result.source] = result.votes

        rows = []
        parties = sorted({key for r in results.values() for key in r.keys()})
        for year in sorted(results.keys(), reverse=True):
            for party_id in parties:
                if party_id not in results[year]:
                    continue
                result = results[year][party_id]
                default_name = result['name_translations'].get(default_locale)
                default_color = self.colors.get(default_name)
                fallback_color = None

                # add the party results
                row = OrderedDict()
                row['domain'] = result['domain'] or self.domain
                row['domain_segment'] = (
                    result['domain_segment']
                    or getattr(self, 'domain_segment', None)
                    or None
                )
                row['year'] = year
                row['id'] = party_id
                row['name'] = default_name
                for locale in locales:
                    name = result['name_translations'].get(locale)
                    fallback_color = fallback_color or self.colors.get(name)
                    row[f'name_{locale}'] = name
                row['total_votes'] = result['total_votes']
                row['color'] = default_color or fallback_color
                row['mandates'] = result['mandates']
                row['votes'] = result['votes']
                row['voters_count'] = convert_decimal(result['voters_count'])
                row['voters_count_percentage'] = convert_decimal(
                    result['voters_count_percentage']
                )

                # add the panachage results
                if self.party_panachage_results.count():
                    for source in parties:
                        column = f'panachage_votes_from_{source}'
                        row[column] = result.get(source, None)
                    row['panachage_votes_from_999'] = result.get('', None)

                rows.append(row)

        return rows
