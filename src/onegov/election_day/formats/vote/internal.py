from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import BALLOT_TYPES
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import STATI
from onegov.election_day.formats.common import validate_integer
from onegov.election_day.formats.mappings import INTERNAL_VOTE_HEADERS
from sqlalchemy.orm import object_session


def import_vote_internal(vote, principal, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by onegov.ballot.Vote.export().

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(
        file, mimetype, expected_headers=INTERNAL_VOTE_HEADERS, dialect='excel'
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
            entity_id = validate_integer(line, 'entity_id')
        except ValueError as e:
            line_errors.append(e.args[0])
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

        # Skip expats if not enabled
        if entity_id == 0 and not vote.expats:
            continue

        # Counted
        counted = line.counted.strip().lower() == 'true'

        # the yeas
        try:
            yeas = validate_integer(line, 'yeas')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the nays
        try:
            nays = validate_integer(line, 'nays')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the eligible voters
        try:
            eligible_voters = validate_integer(line, 'eligible_voters')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the empty votes
        try:
            empty = validate_integer(line, 'empty')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the invalid votes
        try:
            invalid = validate_integer(line, 'invalid')
        except ValueError as e:
            line_errors.append(e.args[0])

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
                dict(
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

    # Add the missing entities
    for ballot_type in ballot_types:
        remaining = set(entities.keys())
        if vote.expats:
            remaining.add(0)
        remaining -= added_entity_ids[ballot_type]
        for entity_id in remaining:
            entity = entities.get(entity_id, {})
            ballot_results[ballot_type].append(
                dict(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=False,
                    entity_id=entity_id
                )
            )

    # Add the results to the DB
    vote.clear_results()
    vote.status = status

    ballot_ids = {b: vote.ballot(b, create=True).id for b in ballot_types}

    session = object_session(vote)
    session.flush()
    session.bulk_insert_mappings(
        BallotResult,
        (
            dict(**result, ballot_id=ballot_ids[ballot_type])
            for ballot_type in ballot_types
            for result in ballot_results[ballot_type]
        )
    )

    return []
