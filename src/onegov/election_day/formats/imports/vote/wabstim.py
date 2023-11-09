from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_integer


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Vote
    from onegov.ballot.types import BallotType
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


WABSTIM_VOTE_HEADERS = (
    'freigegeben',
    'stileer',
    'stiungueltig',
    'stijahg',
    'stineinhg',
    'stiohneawhg',
    'stijan1',
    'stineinn1',
    'stiohneawN1',
    'stijan2',
    'stineinn2',
    'stiohneawN2',
    'stimmberechtigte',
    'bfs',
)


def import_vote_wabstim(
    vote: 'Vote',
    principal: 'Canton | Municipality',
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for municipalities. Since there is no
    format description, importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(
        file, mimetype, expected_headers=WABSTIM_VOTE_HEADERS,
        rename_duplicate_column_names=True
    )
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file,
            mimetype,
            expected_headers=WABSTIM_VOTE_HEADERS,
            encoding='utf-16-le',
            rename_duplicate_column_names=True
        )
        if utf16_error:
            return [error]

    used_ballot_types: list['BallotType'] = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results: dict['BallotType', list[BallotResult]]
    ballot_results = {key: [] for key in used_ballot_types}
    added_entity_ids = set()
    errors: list[FileImportError] = []
    skipped = 0
    entities = principal.entities[vote.date.year]

    assert csv is not None
    for line in csv.lines:
        line_errors = []

        # the id of the entity
        entity_id = None
        try:
            entity_id = validate_integer(line, 'bfs')
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
                added_entity_ids.add(entity_id)

        try:
            counted = True if line.freigegeben else False
        except AttributeError:
            line_errors.append(_("Invalid values"))

        # Skip expats if not enabled
        if entity_id == 0 and not vote.has_expats:
            continue

        # the yeas
        yeas = {}
        try:
            yeas['proposal'] = validate_integer(line, 'stijahg')
            yeas['counter-proposal'] = validate_integer(line, 'stijan1')
            yeas['tie-breaker'] = validate_integer(line, 'stijan2')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the nays
        nays = {}
        try:
            nays['proposal'] = validate_integer(line, 'stineinhg')
            nays['counter-proposal'] = validate_integer(line, 'stineinn1')
            nays['tie-breaker'] = validate_integer(line, 'stineinn2')
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
            e_ballots = validate_integer(line, 'stileer')
            empty['proposal'] = validate_integer(
                line, 'stiohneawhg') + e_ballots
            empty['counter-proposal'] = validate_integer(
                line, 'stiohneawn1') + e_ballots
            empty['tie-breaker'] = validate_integer(
                line, 'stiohneawn2') + e_ballots
        except ValueError as e:
            line_errors.append(e.args[0])

        # the invalid votes
        try:
            invalid = validate_integer(line, 'stiungueltig')
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
            entity = entities.get(entity_id, {})
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        name=entity.get('name', ''),
                        district=entity.get('district', ''),
                        entity_id=entity_id,
                        counted=counted,
                        yeas=yeas[ballot_type] if counted else 0,
                        nays=nays[ballot_type] if counted else 0,
                        eligible_voters=eligible_voters if counted else 0,
                        empty=empty[ballot_type] if counted else 0,
                        invalid=invalid if counted else 0
                    )
                )

    if errors:
        return errors

    if (
        not any((len(results) for results in ballot_results.values())) and not
        skipped
    ):
        return [FileImportError(_("No data found"))]

    vote.clear_results()
    vote.last_result_change = vote.timestamp()

    assert entity_id is not None
    for ballot_type in used_ballot_types:
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= added_entity_ids
        for id in remaining:
            # FIXME: Shouldn't this be entities.get(id, {})?
            entity = entities.get(entity_id, {})
            ballot_results[ballot_type].append(
                BallotResult(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=False,
                    entity_id=id
                )
            )

        if ballot_results[ballot_type]:
            ballot = vote.ballot(ballot_type, create=True)
            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []
