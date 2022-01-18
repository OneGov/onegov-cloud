from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import validate_integer
from onegov.election_day.formats.mappings import WABSTIM_VOTE_HEADERS


def import_vote_wabstim(vote, principal, file, mimetype):
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

    used_ballot_types = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results = {key: [] for key in used_ballot_types}
    added_entity_ids = set()
    errors = []
    skipped = 0
    entities = principal.entities[vote.date.year]

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
        if entity_id == 0 and not vote.expats:
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
            for ballot_type in used_ballot_types:
                entity = entities.get(entity_id, {})
                ballot_results[ballot_type].append(
                    BallotResult(
                        name=entity.get('name', ''),
                        district=entity.get('district', ''),
                        counted=counted,
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

    if (
        not any((len(results) for results in ballot_results.values())) and not
        skipped
    ):
        return [FileImportError(_("No data found"))]

    vote.clear_results()
    vote.last_result_change = vote.timestamp()

    for ballot_type in used_ballot_types:
        remaining = set(entities.keys())
        if vote.expats:
            remaining.add(0)
        remaining -= added_entity_ids
        for id in remaining:
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
