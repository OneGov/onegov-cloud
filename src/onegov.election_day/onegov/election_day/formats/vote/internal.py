from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import BALLOT_TYPES
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import STATI

HEADERS = [
    'status',
    'type',
    'entity_id',
    'counted',
    'yeas',
    'nays',
    'invalid',
    'empty',
    'eligible_voters',
]


def import_vote_internal(vote, principal, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by onegov.ballot.Vote.export().

    :return:
        A list containing errors.

    """
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, dialect='excel'
    )
    if error:
        return [error]

    ballot_results = {}
    errors = []
    added_entity_ids = {}
    ballot_types = set()
    status = 'unknown'
    entities = principal.entities[vote.date.year]

    for line in csv.lines:

        line_errors = []

        status = line.status or 'unknown'
        if status not in STATI:
            line_errors.append(_("Invalid status"))

        ballot_type = line.type
        if ballot_type not in BALLOT_TYPES:
            line_errors.append(_("Invalid ballot type"))
        ballot_types.add(ballot_type)
        added_entity_ids.setdefault(ballot_type, set())
        ballot_results.setdefault(ballot_type, [])

        # the id of the entity
        entity_id = None
        try:
            entity_id = int(line.entity_id or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id not in entities and entity_id in EXPATS:
                entity_id = 0

            if entity_id in added_entity_ids[ballot_type]:
                line_errors.append(
                    _("${name} was found twice", mapping={
                        'name': entity_id
                    }))

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={
                        'name': entity_id
                    }))
            else:
                added_entity_ids[ballot_type].add(entity_id)

        # Counted
        counted = line.counted.strip().lower() == 'true'

        # the yeas
        try:
            yeas = int(line.yeas or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        try:
            nays = int(line.nays or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the eligible voters
        try:
            eligible_voters = int(line.eligible_voters or 0)
        except ValueError:
            line_errors.append(_("Could not read the eligible voters"))

        # the empty votes
        try:
            empty = int(line.empty or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = int(line.invalid or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # now let's do some sanity checks
        try:
            if not eligible_voters:
                line_errors.append(_("No eligible voters"))
            if (yeas + nays + empty + invalid) > eligible_voters:
                line_errors.append(_("More cast votes than eligible voters"))
        except UnboundLocalError:
            pass

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            entity = entities.get(entity_id, {})
            ballot_results[ballot_type].append(
                BallotResult(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=counted,
                    yeas=yeas,
                    nays=nays,
                    eligible_voters=eligible_voters,
                    entity_id=entity_id,
                    empty=empty,
                    invalid=invalid
                )
            )

    if errors:
        return errors

    if not any((len(results) for results in ballot_results.values())):
        return [FileImportError(_("No data found"))]

    vote.clear_results()

    vote.status = status

    for ballot_type in ballot_types:
        remaining = (
            entities.keys() - added_entity_ids[ballot_type]
        )
        for entity_id in remaining:
            entity = entities[entity_id]
            ballot_results[ballot_type].append(
                BallotResult(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=False,
                    entity_id=entity_id
                )
            )

        if ballot_results[ballot_type]:
            ballot = vote.ballot(ballot_type, create=True)
            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []
