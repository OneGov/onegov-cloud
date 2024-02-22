from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_float
from onegov.election_day.formats.imports.common import validate_integer


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Vote
    from onegov.ballot.types import BallotType
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


WABSTI_VOTE_HEADERS = (
    'vorlage-nr.',
    'bfs-nr.',
    'stimmberechtigte',
    'leere sz',
    'ungultige sz',
    'ja',
    'nein',
    'gegenvja',
    'gegenvnein',
    'stichfrja',
    'stichfrnein',
    'stimmbet',
)


def import_vote_wabsti(
    vote: 'Vote',
    principal: 'Canton | Municipality',
    vote_number: int,
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti. Since there is no format description,
    importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(file, mimetype,
                          expected_headers=WABSTI_VOTE_HEADERS)
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype, expected_headers=WABSTI_VOTE_HEADERS,
            encoding='utf-16-le'
        )
        if utf16_error:
            return [error]

    used_ballot_types: list['BallotType'] = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results: dict['BallotType', list[BallotResult]]
    ballot_results = {key: [] for key in used_ballot_types}
    errors: list[FileImportError] = []
    added_entity_ids = set()
    skipped = 0
    entities = principal.entities[vote.date.year]

    assert csv is not None
    for line in csv.lines:

        line_errors = []

        # Skip the results of other votes
        try:
            number = validate_integer(line, 'vorlage_nr_')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            if number != vote_number:
                continue

        # Skip not yet counted results
        try:
            turnout = validate_float(line, 'stimmbet')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            if not turnout:
                skipped += 1
                continue

        # the id of the entity
        entity_id = None
        try:
            entity_id = validate_integer(line, 'bfs_nr_')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            if entity_id not in entities and entity_id in EXPATS:
                entity_id = 0

            if entity_id in added_entity_ids:
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
                name, district, superregion = get_entity_and_district(
                    entity_id, entities, vote, principal, line_errors
                )

            if not line_errors:
                added_entity_ids.add(entity_id)

        # Skip expats if not enabled
        if entity_id == 0 and not vote.has_expats:
            continue

        # the yeas
        yeas = {}
        try:
            yeas['proposal'] = validate_integer(line, 'ja')
            yeas['counter-proposal'] = validate_integer(line, 'gegenvja')
            yeas['tie-breaker'] = validate_integer(line, 'stichfrja')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the nays
        nays = {}
        try:
            nays['proposal'] = validate_integer(line, 'nein')
            nays['counter-proposal'] = validate_integer(line, 'gegenvnein')
            nays['tie-breaker'] = validate_integer(line, 'stichfrnein')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the eligible voters
        try:
            eligible_voters = validate_integer(line, 'stimmberechtigte')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the empty votes
        empty = {}
        try:
            e_ballots = validate_integer(line, 'leere_sz')
            empty['proposal'] = (
                int(getattr(line, 'initoantw', 0) or 0) + e_ballots
            )
            empty['counter-proposal'] = (
                int(getattr(line, 'gegenvoantw', 0) or 0) + e_ballots
            )
            empty['tie-breaker'] = (
                int(getattr(line, 'stichfroantw', 0) or 0) + e_ballots
            )
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = validate_integer(line, 'ungultige_sz')
        except ValueError as e:
            line_errors.append(e.args[0])

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            assert entity_id is not None
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        name=name,
                        district=district,
                        counted=True,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        eligible_voters=eligible_voters,
                        entity_id=entity_id,
                        empty=empty[ballot_type],
                        invalid=invalid
                    )
                )

    if errors:
        return errors

    if not any(ballot_results.values()) and not skipped:
        return [FileImportError(_("No data found"))]

    vote.clear_results()
    vote.last_result_change = vote.timestamp()

    for ballot_type in used_ballot_types:
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= added_entity_ids
        for entity_id in remaining:
            name, district, superregion = get_entity_and_district(
                entity_id, entities, vote, principal
            )
            if vote.domain == 'municipality':
                if principal.domain != 'municipality':
                    if name != vote.domain_segment:
                        continue

            ballot_results[ballot_type].append(
                BallotResult(
                    name=name,
                    district=district,
                    counted=False,
                    entity_id=entity_id
                )
            )

        if ballot_results[ballot_type]:
            ballot = vote.ballot(ballot_type)
            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []
