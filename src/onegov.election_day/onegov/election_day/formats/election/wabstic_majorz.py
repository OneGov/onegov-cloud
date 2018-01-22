from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from uuid import uuid4

HEADERS_WM_WAHL = (
    'sortgeschaeft',  # provides the link to the election
    'absolutesmehr',  # absolute majority
    'ausmittlungsstand',  # complete
)
HEADERS_WMSTATIC_GEMEINDEN = (
    'sortwahlkreis',  # provides the link to the election
    'sortgeschaeft',  # provides the link to the election
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'stimmberechtigte',  # eligible votes
)
HEADERS_WM_GEMEINDEN = (
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'stimmberechtigte',  # eligible votes
    'sperrung',  # counted
    'stmabgegeben',  # received ballots
    'stmleer',  # blank ballots
    'stmungueltig',  # invalid ballots
    'stimmenleer',  # blank votes
    'stimmenungueltig',  # invalid votes
)
HEADERS_WM_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'nachname',  # familiy name
    'vorname',  # first name
    'gewahlt',  # elected
    'partei',  #
)
HEADERS_WM_KANDIDATENGDE = (
    'sortgeschaeft',  # provides the link to the election
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'knr',  # candidate id
    'stimmen',  # votes
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


def import_election_wabstic_majorz(
    election, entities, district, number,
    file_wm_wahl, mimetype_wm_wahl,
    file_wmstatic_gemeinden, mimetype_wmstatic_gemeinden,
    file_wm_gemeinden, mimetype_wm_gemeinden,
    file_wm_kandidaten, mimetype_wm_kandidaten,
    file_wm_kandidatengde, mimetype_wm_kandidatengde
):
    """ Tries to import the files in the given folder.

    We assume that the files there have been uploaded via FTP using the
    WabstiCExport 2.1.

    """
    errors = []

    # Read the files
    wm_wahl, error = load_csv(
        file_wm_wahl, mimetype_wm_wahl,
        expected_headers=HEADERS_WM_WAHL,
        filename='wm_wahl'
    )
    if error:
        errors.append(error)

    wmstatic_gemeinden, error = load_csv(
        file_wmstatic_gemeinden, mimetype_wmstatic_gemeinden,
        expected_headers=HEADERS_WMSTATIC_GEMEINDEN,
        filename='wmstatic_gemeinden'
    )
    if error:
        errors.append(error)

    wm_gemeinden, error = load_csv(
        file_wm_gemeinden, mimetype_wm_gemeinden,
        expected_headers=HEADERS_WM_GEMEINDEN,
        filename='wm_gemeinden'
    )
    if error:
        errors.append(error)

    wm_kandidaten, error = load_csv(
        file_wm_kandidaten, mimetype_wm_kandidaten,
        expected_headers=HEADERS_WM_KANDIDATEN,
        filename='wm_kandidaten'
    )
    if error:
        errors.append(error)

    wm_kandidatengde, error = load_csv(
        file_wm_kandidatengde, mimetype_wm_kandidatengde,
        expected_headers=HEADERS_WM_KANDIDATENGDE,
        filename='wm_kandidatengde'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Parse the election
    absolute_majority = None
    complete = 0
    for line in wm_wahl.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        # Parse the absolute majority
        try:
            absolute_majority = int(line.absolutesmehr or 0)
            complete = int(line.ausmittlungsstand or 0)
            assert 0 <= complete <= 3
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid values"))
        else:
            if absolute_majority == -1:
                absolute_majority = None

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wm_wahl'
                )
                for err in line_errors
            )
            continue

    # Parse the entities
    added_entities = {}
    for line in wmstatic_gemeinden.lines:
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
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id in added_entities:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id}))

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wmstatic_gemeinden'
                )
                for err in line_errors
            )
            continue

        entity = entities.get(entity_id, {})
        added_entities[entity_id] = {
            'name': entity.get('name', ''),
            'district': entity.get('district', ''),
            'elegible_voters': elegible_voters
        }

    for line in wm_gemeinden.lines:
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
                entity = entities.get(entity_id, {})
                added_entities[entity_id] = {
                    'name': entity.get('name', ''),
                    'district': entity.get('district', ''),
                }

        entity = added_entities[entity_id]

        # Check if the entity is counted
        try:
            entity['counted'] = False if int(line.sperrung or 0) == 0 else True
        except ValueError:
            line_errors.append(_("Invalid entity values"))

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
            line_errors.append(_("Invalid entity values"))
        else:
            entity['received_ballots'] = received_ballots
            entity['blank_ballots'] = blank_ballots
            entity['invalid_ballots'] = invalid_ballots
            entity['blank_votes'] = blank_votes
            entity['invalid_votes'] = invalid_votes

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wm_gemeinden'
                )
                for err in line_errors
            )
            continue

    # Parse the candidates
    added_candidates = {}
    for line in wm_kandidaten.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = line.knr
            family_name = line.nachname
            first_name = line.vorname
            elected = True if line.gewahlt == '1' else False
            party = line.partei
        except ValueError:
            line_errors.append(_("Invalid candidate values"))
        else:
            added_candidates[candidate_id] = Candidate(
                id=uuid4(),
                candidate_id=candidate_id,
                family_name=family_name,
                first_name=first_name,
                elected=elected,
                party=party
            )

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wm_kandidaten'
                )
                for err in line_errors
            )
            continue

    # Parse the candidate results
    added_results = {}
    for line in wm_kandidatengde.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            entity_id = get_entity_id(line, entities)
            candidate_id = line.knr
            assert candidate_id in added_candidates
            votes = int(line.stimmen)
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid candidate results"))
        else:
            if entity_id not in added_entities:
                line_errors.append(_("Invalid entity values"))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wm_kandidatengde'
                )
                for err in line_errors
            )
            continue

        if entity_id not in added_results:
            added_results[entity_id] = {}
        added_results[entity_id][candidate_id] = votes

    if errors:
        return errors

    # todo: Add missing entities as uncounted

    if added_results:
        election.clear_results()

        election.absolute_majority = absolute_majority
        election.counted_entities = sum([
            1 for value in added_entities.values() if value['counted']
        ])
        election.total_entities = max(len(entities), len(added_results.keys()))
        election.status = 'unknown'
        if complete == 1:
            election.status = 'interim'
        if complete == 2:
            election.status = 'final'

        for candidate in added_candidates.values():
            election.candidates.append(candidate)

        for entity_id in added_results.keys():
            entity = added_entities[entity_id]
            result = ElectionResult(
                id=uuid4(),
                entity_id=entity_id,
                name=entity['name'],
                district=entity['district'],
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
