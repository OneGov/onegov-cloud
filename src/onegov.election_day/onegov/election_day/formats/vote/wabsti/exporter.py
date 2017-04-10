from onegov.ballot import Ballot, BallotResult
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv
from onegov.election_day.formats.vote import guessed_group
from sqlalchemy.orm import object_session


HEADERS_VOTES_STATIC = (
    'Art',  # domain
    'SortWahlkreis',
    'SortGeschaeft',  # vote number
    'Typ',   # vote type (simple/complex)
)
HEADERS_ENTITIES_STATIC = (
    'Art',  # domain
    'SortWahlkreis',
    'SortGeschaeft',  # vote number
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'Gemeinde',  # group
    'Stimmberechtigte',  # eligible votes
)
HEADERS_ENTITIES = (
    'Art',  # domain
    'SortWahlkreis',
    'SortGeschaeft',  # vote number
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'Sperrung',  # counted
    'Stimmberechtigte',   # eligible votes
    'StmUngueltig',  # invalid
    'StmHGJa',  # yeas (proposal)
    'StmHGNein',  # nays (proposal)
    'StmHGOhneAw',  # empty (proposal)
    'StmN1Ja',  # yeas (counter-proposal)
    'StmN1Nein',  # nays (counter-proposal)
    'StmN1OhneAw',  # empty (counter-proposal)
    'StmN2Ja',  # yeas (tie-breaker)
    'StmN2Nein',  # nays (tie-breaker)
    'StmN2OhneAw',  # empty (tie-breaker)
)


def parse_domain(domain):
    if domain == 'Eidg':
        return 'federation'
    if domain == 'Kant':
        return 'canton'
    if domain == 'Gde':
        return 'municipality'
    return None


def line_is_relevant(line, domain, district, number):
    return (
        parse_domain(line.art) == domain and
        line.sortwahlkreis == district and
        line.sortgeschaeft == number
    )


def import_exporter_files(vote, district, number, entities,
                          file_votes_static, mimetype_votes_static,
                          file_entities_static, mimetype_entities_static,
                          file_entities, mimetype_entities):
    """ Tries to import the files in the given folder.

    We assume that the files there have been uploaded via FTP using the
    WabstiCExport 2.1.

    """
    errors = []

    # Read the files
    votes_static, error = load_csv(
        file_votes_static, mimetype_votes_static,
        expected_headers=HEADERS_VOTES_STATIC,
        filename='votes_static'
    )
    if error:
        errors.append(error)

    entities_static, error = load_csv(
        file_entities_static, mimetype_entities_static,
        expected_headers=HEADERS_ENTITIES_STATIC,
        filename='entities_static'
    )
    if error:
        errors.append(error)

    entities_results, error = load_csv(
        file_entities, mimetype_entities,
        expected_headers=HEADERS_ENTITIES,
        filename='entities_results'
    )
    if error:
        errors.append(error)

    if errors:
        return {'proposal': {'status': 'error', 'errors': errors}}

    # Get the vote type
    domain = vote.domain
    types = [
        line.typ for line in votes_static.lines
        if line_is_relevant(line, domain, district, number)
    ]
    if not len(types):
        errors.append(
            FileImportError(
                _(
                    "The specified vote ('SortWahlkreis'/'SortGeschaeft') is "
                    "not present in the data"
                ),
                filename='votes_static'
            )
        )
        return {'proposal': {'status': 'error', 'errors': errors}}

    used_ballot_types = ['proposal']
    if types[0] == 'SGGVSF':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    # Read the results
    ballot_results = {key: [] for key in used_ballot_types}
    added_entities = {}

    for line in entities_static.lines:
        line_errors = []

        if not line_is_relevant(line, domain, district, number):
            continue

        # Parse the id of the entity
        try:
            entity_id = int(line.sortgemeinde or 0)
            sub_entity_id = int(line.sortgemeindesub or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id not in entities and sub_entity_id in entities:
                entity_id = sub_entity_id

            if entity_id not in entities:
                continue
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id in added_entities:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id}))

        # Parse the name of the entity
        group = line.gemeinde.strip()
        if not group:
            group = entities.get(entity_id, {}).get('name', '')

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='entities_static'
                )
                for err in line_errors
            )
        else:
            added_entities[entity_id] = {
                'group': group,
                'elegible_voters': elegible_voters
            }

    for line in entities_results.lines:
        line_errors = []

        if not line_is_relevant(line, domain, district, number):
            continue

        # Parse the id of the entity
        try:
            entity_id = int(line.sortgemeinde or 0)
            sub_entity_id = int(line.sortgemeindesub or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id not in entities and sub_entity_id in entities:
                entity_id = sub_entity_id

            if entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id not in added_entities:
                added_entities[entity_id] = {
                    'group': entities.get(entity_id, '')
                }

        # Check if the entity is counted
        counted = True
        if int(line.sperrung) == 0:
            counted = False

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))
        else:
            elegible_voters = (
                elegible_voters or
                added_entities.get(entity_id, {}).get('elegible_voters', 0)
            )

        # Parse the invalid votes
        try:
            invalid = int(line.stmungueltig or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # Parse the yeas
        yeas = {}
        try:
            yeas['proposal'] = int(line.stmhgja or 0)
            yeas['counter-proposal'] = int(line.stmn1ja or 0)
            yeas['tie-breaker'] = int(line.stmn2ja or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # Parse the nays
        nays = {}
        try:
            nays['proposal'] = int(line.stmhgnein or 0)
            nays['counter-proposal'] = int(line.stmn1nein or 0)
            nays['tie-breaker'] = int(line.stmn2nein or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # Parse the empty votes
        empty = {}
        try:
            empty['proposal'] = int(line.stmhgohneaw or 0)
            empty['counter-proposal'] = int(line.stmn1ohneaw or 0)
            empty['tie-breaker'] = int(line.stmn2ohneaw or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='entities_results'
                )
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        group=added_entities[entity_id]['group'],
                        counted=counted,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        elegible_voters=elegible_voters,
                        entity_id=entity_id,
                        empty=empty[ballot_type],
                        invalid=invalid
                    )
                )

    if errors:
        return {'proposal': {'status': 'error', 'errors': errors}}

    for ballot_type in used_ballot_types:
        # Add the entities present in the static data but not in the results
        remaining = (
            added_entities.keys() -
            set(result.entity_id for result in ballot_results[ballot_type])
        )
        for entity_id in remaining:
            ballot_results[ballot_type].append(
                BallotResult(
                    entity_id=entity_id,
                    group=added_entities[entity_id]['group'],
                    counted=False,
                )
            )

        # Add the entities missing entirely
        remaining = (
            entities.keys() -
            set(result.entity_id for result in ballot_results[ballot_type])
        )
        for entity_id in remaining:
            entity = entities[entity_id]
            ballot_results[ballot_type].append(
                BallotResult(
                    entity_id=entity_id,
                    group=guessed_group(entity, ballot_results[ballot_type]),
                    counted=False,
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
            'records': len(added_entities)
        } for ballot_type in used_ballot_types
    }
