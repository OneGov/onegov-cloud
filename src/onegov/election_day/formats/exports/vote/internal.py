from __future__ import annotations

from collections import OrderedDict


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.models import Vote


def export_vote_internal(
    vote: Vote,
    locales: Collection[str]
) -> list[dict[str, Any]]:
    """ Returns all data connected to this vote as list with dicts.

    This is meant as a base for json/csv/excel exports. The result is
    therefore a flat list of dictionaries with repeating values to avoid
    the nesting of values. Each record in the resulting list is a single
    ballot result.

    """

    rows: list[dict[str, Any]] = []
    answer = vote.answer
    short_titles = vote.short_title_translations or {}

    for ballot in sorted(vote.ballots, key=lambda b: b.type):
        titles = (
            ballot.title_translations or vote.title_translations or {}
        )
        for result in sorted(ballot.results, key=lambda r: r.entity_id):
            row: dict[str, Any] = OrderedDict()
            row['id'] = vote.id
            for locale in locales:
                title = titles.get(locale, '') or ''
                row[f'title_{locale}'] = title.strip()
            for locale in locales:
                title = short_titles.get(locale, '') or ''
                row[f'short_title_{locale}'] = title.strip()
            row['date'] = vote.date.isoformat()
            row['shortcode'] = vote.shortcode
            row['domain'] = vote.domain
            row['status'] = vote.status or 'unknown'
            row['answer'] = answer
            row['type'] = ballot.type
            row['ballot_answer'] = ballot.answer
            row['district'] = result.district or ''
            row['name'] = result.name
            row['entity_id'] = result.entity_id
            row['counted'] = result.counted
            row['yeas'] = result.yeas
            row['nays'] = result.nays
            row['invalid'] = result.invalid
            row['empty'] = result.empty
            row['eligible_voters'] = result.eligible_voters
            row['expats'] = result.expats or ''

            rows.append(row)

    return rows
