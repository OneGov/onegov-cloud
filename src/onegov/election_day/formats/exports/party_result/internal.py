from collections import OrderedDict


def export_parties_internal(
    item, locales, default_locale, json_serializable=False
):
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


def _export_parties(item, locales, default_locale, json_serializable=False,
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
    for result in item.party_results:
        if result.domain != (domain or item.domain):
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
    if domain == item.domain:
        for result in item.party_panachage_results:
            year = results.setdefault(item.date.year, {})
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
            if item.party_panachage_results.count():
                for source in parties:
                    column = f'panachage_votes_from_{source}'
                    row[column] = result.get(source, None)
                row['panachage_votes_from_999'] = result.get('', None)

            rows.append(row)

    return rows