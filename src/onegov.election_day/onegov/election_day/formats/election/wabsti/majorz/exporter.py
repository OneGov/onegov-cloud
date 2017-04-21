from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats import EXPATS
from onegov.election_day.formats import FileImportError
from onegov.election_day.formats import load_csv
from onegov.election_day.formats.election import clear_election
from uuid import uuid4


HEADERS_ENTITIES_STATIC = (
    'SortWahlkreis',  # provides the link to the election
    'SortGeschaeft',  # provides the link to the election
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'Gemeinde',  # group
    'Stimmberechtigte',  # eligible votes
)
HEADERS_ENTITIES = (
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'Stimmberechtigte',  # eligible votes
    'Sperrung',  # counted
    'StmAbgegeben',  # received ballots
    'StmLeer',  # blank ballots
    'StmUngueltig',  # invalid ballots
    'StimmenLeer',  # blank votes
    'StimmenUngueltig',  # invalid votes
)
HEADERS_CANDIDATES = (
    'SortGeschaeft',  # provides the link to the election
    'KNR',  # candidate id
    'Nachname',  # familiy name
    'Vorname',  # first name
    'Gewahlt',  # elected
)
HEADERS_CANDIDATE_RESULTS = (
    'SortGeschaeft',  # provides the link to the election
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'KNR',  # candidate id
    'Stimmen',  # votes
)


def line_is_relevant(line, number, district=None):
    # why is 'SortWahlkreis' only in the static file??!
    if district:
        return line.sortwahlkreis == district and line.sortgeschaeft == number
    else:
        return line.sortgeschaeft == number


def get_entity_id(line, entities):
    entity_id = int(line.sortgemeinde or 0)
    sub_entity_id = int(line.sortgemeindesub or 0)
    if entity_id not in entities:
        if sub_entity_id in entities:
            entity_id = sub_entity_id
        elif entity_id in EXPATS or sub_entity_id in EXPATS:
            entity_id = 0
    return entity_id


def import_exporter_files(election, district, number, entities,
                          file_entities_static, mimetype_entities_static,
                          file_entities, mimetype_entities,
                          file_candidates, mimetype_candidates,
                          file_candidate_results, mimetype_candidate_results):
    """ Tries to import the files in the given folder.

    We assume that the files there have been uploaded via FTP using the
    WabstiCExport 2.1.

    """
    errors = []

    # Read the files
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

    candidates, error = load_csv(
        file_candidates, mimetype_candidates,
        expected_headers=HEADERS_CANDIDATES,
        filename='candidates'
    )
    if error:
        errors.append(error)

    candidate_results, error = load_csv(
        file_candidate_results, mimetype_candidate_results,
        expected_headers=HEADERS_CANDIDATE_RESULTS,
        filename='candidate_results'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Read the results
    added_entities = {}

    for line in entities_static.lines:
        line_errors = []

        if not line_is_relevant(line, number, district=district):
            continue

        # Parse the id of the entity
        try:
            entity_id = get_entity_id(line, entities)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id and entity_id not in entities:
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
            continue
        else:
            added_entities[entity_id] = {
                'group': group,
                'elegible_voters': elegible_voters
            }

    for line in entities_results.lines:
        line_errors = []

        # Why is there no 'SortGeschaeft'??!
        # if not line_is_relevant(line, number):
        #     continue

        # Parse the id of the entity
        try:
            entity_id = get_entity_id(line, entities)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id not in added_entities:
                added_entities[entity_id] = {
                    'group': entities.get(entity_id, {}).get('name', '')
                }

        entity = added_entities[entity_id]

        # Check if the entity is counted
        entity['counted'] = False if int(line.sperrung) == 0 else True

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Invalid entity values"))
        else:
            elegible_voters = (
                elegible_voters or
                added_entities.get(entity_id, {}).get('elegible_voters', 0)
            )
            entity['elegible_voters'] = elegible_voters

        # Parse the ballots and votes
        try:
            received_ballots = int(line.stmabgegeben or 0)
            blank_ballots = int(line.stmleer or 0)
            invalid_ballots = int(line.stmungueltig or 0)
            blank_votes = int(line.stimmenleer or 0)
            invalid_votes = int(line.stimmenungueltig or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))
        else:
            entity['received_ballots'] = received_ballots
            entity['blank_ballots'] = blank_ballots
            entity['invalid_ballots'] = invalid_ballots
            entity['blank_votes'] = blank_votes
            entity['invalid_votes'] = invalid_votes

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='entities_results'
                )
                for err in line_errors
            )
            continue

    added_candidates = {}
    for line in candidates.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = line.knr
            family_name = line.nachname
            first_name = line.vorname
            elected = True if line.gewahlt == '1' else False
        except ValueError:
            line_errors.append(_("Invalid candidate values"))
        else:
            added_candidates[candidate_id] = Candidate(
                id=uuid4(),
                candidate_id=candidate_id,
                family_name=family_name,
                first_name=first_name,
                elected=elected
            )

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='candidates'
                )
                for err in line_errors
            )
            continue

    added_results = {}
    for line in candidate_results.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            entity_id = get_entity_id(line, entities)
            candidate_id = line.knr
            votes = int(line.stimmen)
        except ValueError:
            line_errors.append(_("Invalid candidate results"))
        else:
            if entity_id not in added_entities:
                line_errors.append(_("Invalid entity values"))
            if candidate_id not in added_candidates:
                line_errors.append(_("Invalid candidate values"))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='candidate_results'
                )
                for err in line_errors
            )
            continue

        if entity_id not in added_results:
            added_results[entity_id] = {}
        added_results[entity_id][candidate_id] = votes

    if errors:
        return errors

    if added_results:
        clear_election(election)

        election.counted_entities = len(added_results.keys())
        election.total_entities = len(entities)

        for candidate in added_candidates.values():
            election.candidates.append(candidate)

        for entity_id in added_results.keys():
            entity = added_entities[entity_id]
            result = ElectionResult(
                id=uuid4(),
                entity_id=entity_id,
                group=entity['group'],
                elegible_voters=entity['elegible_voters'],
                received_ballots=entity['received_ballots'],
                blank_ballots=entity['blank_ballots'],
                invalid_ballots=entity['invalid_ballots'],
                blank_votes=entity['blank_votes'],
                invalid_votes=entity['invalid_votes']
            )
            for candidate_id, votes in added_results[entity_id].items():
                result.candidate_results.append(
                    CandidateResult(
                        votes=votes,
                        candidate_id=added_candidates[candidate_id].id
                    )
                )
            election.results.append(result)

    return []
