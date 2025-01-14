from __future__ import annotations

from collections import OrderedDict


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from decimal import Decimal
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import ProporzElection


def export_parties_internal(
    item: ElectionCompound | ProporzElection,
    locales: Collection[str],
    default_locale: str,
    json_serializable: bool = False
) -> list[dict[str, Any]]:
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
    parts = {(r.domain, r.domain_segment) for r in item.party_results}
    for domain, domain_segment in sorted(parts):
        result.extend(
            _export_parties(
                item,
                locales, default_locale,
                json_serializable,
                domain, domain_segment
            )
        )
    return result


def _export_parties(
    item: ElectionCompound | ProporzElection,
    locales: Collection[str],
    default_locale: str,
    json_serializable: bool = False,
    domain: str | None = None,
    domain_segment: str | None = None
) -> list[dict[str, Any]]:
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

    def convert_decimal(value: Decimal | None) -> float | str | None:
        if value is None:
            return value
        if json_serializable:
            return float(value)
        return str(value)

    results: dict[int, dict[str, dict[str, Any]]] = {}

    # get the party results
    for party_result in item.party_results:
        if party_result.domain != (domain or item.domain):
            continue
        if domain_segment and party_result.domain_segment != domain_segment:
            continue
        results_per_year = results.setdefault(party_result.year, {})
        results_per_year[party_result.party_id] = {
            'domain': party_result.domain,
            'domain_segment': party_result.domain_segment,
            'name_translations': party_result.name_translations,
            'total_votes': party_result.total_votes,
            'mandates': party_result.number_of_mandates,
            'votes': party_result.votes,
            'voters_count': party_result.voters_count,
            'voters_count_percentage': party_result.voters_count_percentage
        }

    # get the panachage results
    if domain == item.domain:
        for panachage_result in item.party_panachage_results:
            results_per_year = results.setdefault(item.date.year, {})
            target = results_per_year.setdefault(panachage_result.target, {})
            target[panachage_result.source] = panachage_result.votes

    rows: list[dict[str, Any]] = []
    parties = sorted({key for r in results.values() for key in r.keys()})
    for year in sorted(results.keys(), reverse=True):
        for party_id in parties:
            if party_id not in results[year]:
                continue
            result = results[year][party_id]
            default_name = result['name_translations'].get(default_locale)
            default_color = item.colors.get(default_name)
            fallback_color = None

            # add the party results
            row = OrderedDict()
            row['domain'] = result['domain'] or item.domain
            row['domain_segment'] = (
                result['domain_segment']
                or getattr(item, 'domain_segment', None)
                or None
            )
            row['year'] = year
            row['id'] = party_id
            row['name'] = default_name
            for locale in locales:
                name = result['name_translations'].get(locale)
                fallback_color = fallback_color or item.colors.get(name)
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
            if item.party_panachage_results:
                for source in parties:
                    column = f'panachage_votes_from_{source}'
                    row[column] = result.get(source, None)
                row['panachage_votes_from_999'] = result.get('', None)

            rows.append(row)

    return rows
