from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_integer
from onegov.election_day.models import BallotResult
from sqlalchemy.orm import object_session


from typing import Any
from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.models import Vote
    from onegov.election_day.types import BallotType

    # TODO: TypedDict for BallotResult


WABSTIC_VOTE_HEADERS_SG_GESCHAEFTE = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    # 'ausmittlungsstand',  # for status, old
    # 'anzgdependent',  # for status, new
    # 'anzpendentgde',  # for status, latest
)

WABSTIC_VOTE_HEADERS_SG_GEMEINDEN = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    'bfsnrgemeinde',  # BFS
    'sperrung',  # counted
    'stimmberechtigte',   # eligible votes
    'stmungueltig',  # invalid
    'stmleer',  # empty (proposal if simple)
    'stmhgja',  # yeas (proposal)
    'stmhgnein',  # nays (proposal)
    'stmhgohneaw',  # empty (proposal if complex)
    'stmn1ja',  # yeas (counter-proposal)
    'stmn1nein',  # nays (counter-proposal)
    'stmn1ohneaw',  # empty (counter-proposal)
    'stmn2ja',  # yeas (tie-breaker)
    'stmn2nein',  # nays (tie-breaker)
    'stmn2ohneaw',  # empty (tie-breaker)
)


def parse_domain(domain: str) -> str | None:
    if domain in ('Eidg', 'CH'):
        return 'federation'
    if domain in ('Kant', 'CT'):
        return 'canton'
    if domain in ('Gde', 'MU'):
        return 'municipality'
    return None


def line_is_relevant(
    line: DefaultRow,
    domain: str,
    district: str,
    number: str
) -> bool:
    return (
        parse_domain(line.art) == domain
        and line.sortwahlkreis == district
        and line.sortgeschaeft == number
    )


def import_vote_wabstic(
    vote: Vote,
    principal: Canton | Municipality,
    number: str,
    district: str,
    file_sg_geschaefte: IO[bytes],
    mimetype_sg_geschaefte: str,
    file_sg_gemeinden: IO[bytes],
    mimetype_sg_gemeinden: str
) -> list[FileImportError]:
    """ Tries to import the given CSV files from a WabstiCExport.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """
    errors = []
    entities = principal.entities[vote.date.year]

    # Read the files
    sg_geschaefte, error = load_csv(
        file_sg_geschaefte, mimetype_sg_geschaefte,
        expected_headers=WABSTIC_VOTE_HEADERS_SG_GESCHAEFTE,
        filename='sg_geschaefte'
    )
    if error:
        errors.append(error)

    sg_gemeinden, error = load_csv(
        file_sg_gemeinden, mimetype_sg_gemeinden,
        expected_headers=WABSTIC_VOTE_HEADERS_SG_GEMEINDEN,
        filename='sg_gemeinden'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Get the vote type
    used_ballot_types: list[BallotType] = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    # Parse the vote
    remaining_entities = None
    assert sg_geschaefte is not None
    for line in sg_geschaefte.lines:
        line_errors: list[str] = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue

        remaining_entities = None
        try:
            if hasattr(line, 'anzpendentgde'):
                remaining_entities = validate_integer(
                    line, 'anzpendentgde', default=None
                )
            else:
                remaining_entities = validate_integer(
                    line, 'anzgdependent', default=None
                )
        except Exception as e:
            line_errors.append(
                _('Error in anzpendentgde/anzgdependent: ${msg}',
                  mapping={'msg': e.args[0]}))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='sg_geschaefte'
                )
                for err in line_errors
            )
            continue

    # Parse the results
    ballot_results: dict[BallotType, list[dict[str, Any]]]
    ballot_results = {key: [] for key in used_ballot_types}
    added_entities = []
    assert sg_gemeinden is not None
    for line in sg_gemeinden.lines:
        line_errors = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue

        # Parse the id of the entity
        entity_id = None
        entity_name = ''
        entity_district = None
        try:
            entity_id = validate_integer(line, 'bfsnrgemeinde')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            entity_id = 0 if entity_id in EXPATS else entity_id

            if entity_id in added_entities:
                line_errors.append(
                    _('${name} was found twice', mapping={'name': entity_id}))
            else:
                added_entities.append(entity_id)

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _('${name} is unknown', mapping={'name': entity_id}))
            else:
                entity_name, entity_district, _superregion = (
                    get_entity_and_district(
                        entity_id, entities, vote, principal, line_errors
                    )
                )

        # Skip expats if not enabled
        if entity_id == 0 and not vote.has_expats:
            continue

        # Check if the entity is counted
        try:
            counted_num = validate_integer(line, 'sperrung')
            counted = counted_num != 0
        except ValueError:
            line_errors.append(_('Invalid values'))
        else:
            if not counted:
                continue

        # Parse the eligible voters
        try:
            eligible_voters = validate_integer(line, 'stimmberechtigte')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the invalid votes
        try:
            invalid = validate_integer(line, 'stmungueltig')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the yeas
        yeas = {}
        try:
            yeas['proposal'] = validate_integer(line, 'stmhgja')
            yeas['counter-proposal'] = validate_integer(line, 'stmn1ja')
            yeas['tie-breaker'] = validate_integer(line, 'stmn2ja')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the nays
        nays = {}
        try:
            nays['proposal'] = validate_integer(line, 'stmhgnein')
            nays['counter-proposal'] = validate_integer(line, 'stmn1nein')
            nays['tie-breaker'] = validate_integer(line, 'stmn2nein')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the empty votes
        empty = {}
        try:
            empty['proposal'] = (
                validate_integer(line, 'stmleer')
                or validate_integer(line, 'stmhgohneaw')
            )
            empty['counter-proposal'] = validate_integer(line, 'stmn1ohneaw')
            empty['tie-breaker'] = validate_integer(line, 'stmn2ohneaw')
        except ValueError:
            line_errors.append(_('Could not read the empty votes'))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='sg_gemeinden'
                )
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    {
                        'entity_id': entity_id,
                        'name': entity_name,
                        'district': entity_district,
                        'counted': counted,
                        'eligible_voters': eligible_voters,
                        'invalid': invalid,
                        'yeas': yeas[ballot_type],
                        'nays': nays[ballot_type],
                        'empty': empty[ballot_type]
                    }
                )

    if errors:
        return errors

    # Add the missing entities
    for ballot_type in used_ballot_types:
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= {r['entity_id'] for r in ballot_results[ballot_type]}
        for entity_id in remaining:
            entity_name, entity_district, _superregion = (
                get_entity_and_district(
                    entity_id, entities, vote, principal
                )
            )
            if vote.domain == 'municipality':
                if principal.domain != 'municipality':
                    if entity_name != vote.domain_segment:
                        continue

            ballot_results[ballot_type].append(
                {
                    'entity_id': entity_id,
                    'name': entity_name,
                    'district': entity_district,
                    'counted': False,
                }
            )

    # Add the results to the DB
    vote.clear_results()
    vote.last_result_change = vote.timestamp()
    vote.status = 'unknown'

    if remaining_entities == 0:
        vote.status = 'final'

    ballot_ids = {b: vote.ballot(b).id for b in used_ballot_types}

    session = object_session(vote)
    session.flush()
    session.bulk_insert_mappings(
        BallotResult,
        (
            dict(**result, ballot_id=ballot_ids[ballot_type])
            for ballot_type in used_ballot_types
            for result in ballot_results[ballot_type]
        )
    )
    session.expire(vote)

    return []
