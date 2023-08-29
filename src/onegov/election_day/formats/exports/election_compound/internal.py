from collections import OrderedDict
from onegov.election_day.formats.exports.election import \
    export_election_internal


def export_election_compound_internal(compound, locales):
    """ Returns all data connected to this election compound as list with
    dicts.

    This is meant as a base for json/csv/excel exports. The result is
    therefore a flat list of dictionaries with repeating values to avoid
    the nesting of values. Each record in the resulting list is a single
    candidate result for each political entity. Party results are not
    included in the export (since they are not really connected with the
    lists).

    If consider completed, status for candidate_elected and
    absolute_majority will be set to None if election is not completed.

    """

    common = OrderedDict()
    for locale in locales:
        common[f'compound_title_{locale}'] = compound.title_translations.get(
            locale, ''
        )
    common['compound_date'] = compound.date.isoformat()
    common['compound_mandates'] = compound.number_of_mandates

    rows = []
    for election in compound.elections:
        for row in export_election_internal(election, locales):
            rows.append(
                OrderedDict(list(common.items()) + list(row.items()))
            )
    return rows
