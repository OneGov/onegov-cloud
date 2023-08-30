from collections import OrderedDict


def export_vote_internal(vote, locales):
    """ Returns all data connected to this vote as list with dicts.

    This is meant as a base for json/csv/excel exports. The result is
    therefore a flat list of dictionaries with repeating values to avoid
    the nesting of values. Each record in the resulting list is a single
    ballot result.

    """

    rows = []

    for ballot in vote.ballots:
        for result in ballot.results:
            row = OrderedDict()

            titles = (
                ballot.title_translations or vote.title_translations or {}
            )
            for locale in locales:
                row[f'title_{locale}'] = titles.get(locale, '')
            row['date'] = vote.date.isoformat()
            row['shortcode'] = vote.shortcode
            row['domain'] = vote.domain
            row['status'] = vote.status or 'unknown'
            row['type'] = ballot.type
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