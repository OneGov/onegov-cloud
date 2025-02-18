from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import BALLOT_TYPES
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import STATI
from onegov.election_day.formats.imports.common import validate_integer
from onegov.election_day.models import BallotResult


from typing import cast
from typing import Any
from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.models import Vote
    from onegov.election_day.types import BallotType
    from onegov.election_day.types import Status

    # TODO: Add TypedDict for BallotResult


INTERNAL_VOTE_HEADERS = (
    'status',
    'type',
    'entity_id',
    'counted',
    'yeas',
    'nays',
    'invalid',
    'empty',
    'eligible_voters',
)


def import_vote_internal(
    vote: Vote,
    principal: Canton | Municipality,
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
    """ Tries to import the given csv, xls or xlsx file.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(
        file, mimetype, expected_headers=INTERNAL_VOTE_HEADERS, dialect='excel'
    )
    if error:
        return [error]

    ballot_results: dict[str, list[dict[str, Any]]] = {}
    errors: list[FileImportError] = []
    added_entity_ids: dict[str, set[int]] = {}
    status = 'unknown'
    entities = principal.entities[vote.date.year]

    assert csv is not None
    for line in csv.lines:

        line_errors: list[str] = []

        status = line.status or 'unknown'
        if status not in STATI:
            line_errors.append(_('Invalid status'))

        ballot_type = line.type
        if ballot_type not in BALLOT_TYPES:
            line_errors.append(_('Invalid ballot type'))
        if vote.type == 'simple':
            ballot_type = 'proposal'

        added_entity_ids.setdefault(ballot_type, set())
        ballot_results.setdefault(ballot_type, [])

        # the id of the entity
        entity_id = None
        name = ''
        district = None
        try:
            entity_id = validate_integer(line, 'entity_id')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            if entity_id not in entities and entity_id in EXPATS:
                entity_id = 0

            if entity_id in added_entity_ids[ballot_type]:
                line_errors.append(
                    _('${name} was found twice', mapping={
                        'name': entity_id
                    }))

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _('${name} is unknown', mapping={
                        'name': entity_id
                    }))
            else:
                name, district, _superregion = get_entity_and_district(
                    entity_id, entities, vote, principal, line_errors
                )

            if not line_errors:
                added_entity_ids[ballot_type].add(entity_id)

        # Skip expats if not enabled
        if entity_id == 0 and not vote.has_expats:
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

        # the expats
        try:
            expats = validate_integer(
                line, 'expats', optional=True, default=None
            ) or validate_integer(
                line, 'entity_expats', optional=True, default=None
            )
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
        if counted:
            try:
                if not eligible_voters:
                    line_errors.append(_('No eligible voters'))
                if (yeas + nays + empty + invalid) > eligible_voters:
                    line_errors.append(
                        _('More cast votes than eligible voters')
                    )
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
            ballot_results[ballot_type].append(
                {
                    'name': name,
                    'district': district,
                    'entity_id': entity_id,
                    'counted': counted,
                    'yeas': yeas if counted else 0,
                    'nays': nays if counted else 0,
                    'eligible_voters': eligible_voters if counted else 0,
                    'expats': expats if counted else 0,
                    'empty': empty if counted else 0,
                    'invalid': invalid if counted else 0
                }
            )

    if errors:
        return errors

    if not any(ballot_results.values()):
        return [FileImportError(_('No data found'))]

    # if there were no errors we know we have a valid status and ballot_types
    status = cast('Status', status)
    ballot_types = cast('Collection[BallotType]', ballot_results.keys())

    # Add the missing entities
    for ballot_type in ballot_types:
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= added_entity_ids[ballot_type]
        for entity_id in remaining:
            name, district, _superregion = get_entity_and_district(
                entity_id, entities, vote, principal
            )
            if vote.domain == 'none':
                continue
            if vote.domain == 'municipality':
                if principal.domain != 'municipality':
                    if name != vote.domain_segment:
                        continue

            ballot_results[ballot_type].append(
                {
                    'name': name,
                    'district': district,
                    'counted': False,
                    'entity_id': entity_id,
                    'yeas': 0,
                    'nays': 0,
                    'eligible_voters': 0,
                    'expats': None,
                    'empty': 0,
                    'invalid': 0
                }
            )

    vote.last_result_change = vote.timestamp()
    vote.status = status

    # Add the results to the DB
    for ballot_type in ballot_types:
        ballot = vote.ballot(ballot_type)
        existing = {result.entity_id: result for result in ballot.results}
        for result in ballot_results[ballot_type]:
            entity_id = result['entity_id']
            if entity_id in existing:
                for key, value in result.items():
                    setattr(existing[entity_id], key, value)
            else:
                ballot.results.append(BallotResult(**result))

        # Remove obsolete results
        obsolete = (
            set(existing.keys())
            - {result['entity_id'] for result in ballot_results[ballot_type]}
        )
        for entity_id in obsolete:
            ballot.results.remove(existing[entity_id])

    return []
