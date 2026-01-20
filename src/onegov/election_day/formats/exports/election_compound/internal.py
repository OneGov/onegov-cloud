from __future__ import annotations

from collections import OrderedDict
from itertools import chain
from onegov.election_day.formats.exports.election import (
    export_election_internal)


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.models import ElectionCompound


def export_election_compound_internal(
    compound: ElectionCompound,
    locales: Collection[str]
) -> list[dict[str, Any]]:
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

    titles = compound.title_translations or {}
    short_titles = compound.short_title_translations or {}

    common: dict[str, Any] = OrderedDict()
    common['compound_id'] = compound.id
    for locale in locales:
        title = titles.get(locale, '') or ''
        common[f'compound_title_{locale}'] = title.strip()
    for locale in locales:
        title = short_titles.get(locale, '') or ''
        common[f'compound_short_title_{locale}'] = title.strip()
    common['compound_date'] = compound.date.isoformat()
    common['compound_mandates'] = compound.number_of_mandates

    return [
        OrderedDict(chain(common.items(), row.items()))
        for election in compound.elections
        for row in export_election_internal(election, locales)
    ]
