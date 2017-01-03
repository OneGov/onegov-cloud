from onegov.ballot import Ballot, BallotResult
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv
from sqlalchemy.orm import object_session


HEADERS = [
    'Vorlage-Nr.',
    'Gemeinde',
    'BfS-Nr.',
    'Stimmberechtigte',
    'leere SZ',
    'ungültige SZ',
    'Ja',
    'Nein',
    'GegenvJa',
    'GegenvNein',
    'StichfrJa',
    'StichfrNein',
    'StimmBet',
]


def import_file(municipalities, vote, file, mimetype, vote_number, complex):
    """ Tries to import the given csv, xls or xlsx file.

    :return: A dictionary of dictionaries containing the status and a list of
    errors if any.

    For example::

        {'proposal': {'status': 'ok', 'errors': []}}

    """
    csv, error = load_csv(file, mimetype, expected_headers=HEADERS)
    if error:
        return {'proposal': {'status': 'error', 'errors': [error]}}

    used_ballot_types = ['proposal']
    if complex:
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results = {key: [] for key in used_ballot_types}
    errors = []
    added_entity_ids = set()
    added_groups = set()

    skipped = 0

    for line in csv.lines:

        if int(line.vorlage_nr_ or 0) != vote_number:
            continue

        if not float(line.stimmbet or 0):
            skipped += skipped
            continue

        line_errors = []

        # the name of the municipality
        group = line.gemeinde.strip()
        if not group:
            line_errors.append(_("Missing municipality"))
        if group in added_groups:
            line_errors.append(_("${group} was found twice", mapping={
                'group': group
            }))
        added_groups.add(group)

        # the id of the municipality
        try:
            entity_id = int(line.bfs_nr_ or 0)
        except ValueError:
            line_errors.append(_("Invalid municipality id"))
        else:
            if entity_id in added_entity_ids:
                line_errors.append(
                    _("municipality id ${id} was found twice", mapping={
                        'id': entity_id
                    }))

            if entity_id not in municipalities:
                if line.gemeinde.strip() == 'Auslandschweizer':
                    # https://github.com/OneGov/onegov.election_day/issues/40
                    entity_id = 0
                    added_entity_ids.add(entity_id)
                else:
                    line_errors.append(
                        _("municipality id ${id} is unknown", mapping={
                            'id': entity_id
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

        # the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # the empty votes
        try:
            empty = int(line.leere_sz or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))
        # the invalid votes
        try:
            invalid = int(line.ungultige_sz or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # now let's do some sanity checks
        try:
            if not elegible_voters:
                line_errors.append(_("No elegible voters"))
            up = elegible_voters - empty - invalid
            if (
                ((yeas['proposal'] + nays['proposal']) > up) or
                ((yeas['counter-proposal'] + nays['counter-proposal']) > up) or
                ((yeas['tie-breaker'] + nays['tie-breaker']) > up)
            ):
                line_errors.append(_("More cast votes than elegible voters"))
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
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        group=group,
                        counted=True,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        elegible_voters=elegible_voters,
                        entity_id=entity_id,
                        empty=empty,
                        invalid=invalid
                    )
                )

    if errors:
        return {'proposal': {'status': 'error', 'errors': errors}}

    if (
        not any((len(results) for results in ballot_results.values())) and not
        skipped
    ):
        return {
            'proposal': {
                'status': 'fail',
                'errors': [FileImportError(_("No data found"))],
                'records': 0
            }
        }

    for ballot_type in used_ballot_types:
        remaining = (
            municipalities.keys() - added_entity_ids
        )
        for id in remaining:
            municipality = municipalities[id]
            ballot_results[ballot_type].append(
                BallotResult(
                    group=municipality['name'],
                    counted=False,
                    entity_id=id
                )
            )

        if ballot_results[ballot_type]:
            ballot = next(
                (b for b in vote.ballots if b.type == ballot_type), None
            )
            if not ballot:
                ballot = Ballot(type=ballot_type)
                vote.ballots.append(ballot)
            session = object_session(vote)
            for result in ballot.results:
                session.delete(result)
            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return {
        ballot_type: {
            'status': 'ok',
            'errors': errors if ballot_type == 'proposal' else [],
            'records': len(added_entity_ids)
        } for ballot_type in used_ballot_types
    }
