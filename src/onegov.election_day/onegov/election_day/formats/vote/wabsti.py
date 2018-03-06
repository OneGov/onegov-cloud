from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv


HEADERS = (
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


def import_vote_wabsti(vote, principal, vote_number, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti. Since there is no format description,
    importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(file, mimetype, expected_headers=HEADERS)
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype, expected_headers=HEADERS, encoding='utf-16-le'
        )
        if utf16_error:
            return [error]

    used_ballot_types = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results = {key: [] for key in used_ballot_types}
    errors = []
    added_entity_ids = set()
    skipped = 0
    entities = principal.entities[vote.date.year]

    for line in csv.lines:

        line_errors = []

        # Skip the results of other votes
        try:
            number = int(line.vorlage_nr_ or 0)
        except ValueError:
            line_errors.append(_("Invalid values"))
        else:
            if number != vote_number:
                continue

        # Skip not yet counted results
        try:
            turnout = float(line.stimmbet or 0)
        except ValueError:
            line_errors.append(_("Invalid values"))
        else:
            if not turnout:
                skipped += 1
                continue

        # the id of the entity
        entity_id = None
        try:
            entity_id = int(line.bfs_nr_ or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
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

        # the yeas
        yeas = {}
        try:
            yeas['proposal'] = int(line.ja or 0)
            yeas['counter-proposal'] = int(line.gegenvja or 0)
            yeas['tie-breaker'] = int(line.stichfrja or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        nays = {}
        try:
            nays['proposal'] = int(line.nein or 0)
            nays['counter-proposal'] = int(line.gegenvnein or 0)
            nays['tie-breaker'] = int(line.stichfrnein or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the eligible voters
        try:
            eligible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the eligible voters"))
        else:
            # Ignore the expats if no eligible voters
            if not entity_id and not eligible_voters:
                continue

        # the empty votes
        empty = {}
        try:
            e_ballots = int(line.leere_sz or 0)
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
            invalid = int(line.ungultige_sz or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

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

    if (
        not any((len(results) for results in ballot_results.values())) and not
        skipped
    ):
        return [FileImportError(_("No data found"))]

    vote.clear_results()

    for ballot_type in used_ballot_types:
        remaining = (
            entities.keys() - added_entity_ids
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
