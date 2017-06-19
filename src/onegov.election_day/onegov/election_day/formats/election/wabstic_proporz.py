from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.utils import clear_election
from uuid import uuid4


HEADERS_WP_WAHL = (
    'sortgeschaeft',  # provides the link to the election
    'ausmittlungsstand',  # complete
)
HEADERS_WPSTATIC_GEMEINDEN = (
    'sortwahlkreis',  # provides the link to the election
    'sortgeschaeft',  # provides the link to the election
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'stimmberechtigte',  # eligible votes
)
HEADERS_WP_GEMEINDEN = (
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'stimmberechtigte',  # eligible votes
    'sperrung',  # counted
    'stmabgegeben',  # received ballots
    'stmleer',  # blank ballots
    'stmungueltig',  # invalid ballots
    'anzwzamtleer',  # blank ballots
)
HEADERS_WP_LISTEN = (
    'sortgeschaeft',  # provides the link to the election
    'listnr',
    'listcode',
    'sitze',
    'listverb',
    'listuntverb',
)
HEADERS_WP_LISTENGDE = (
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'listnr',
    'stimmentotal',
)
HEADERS_WPSTATIC_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'nachname',  # familiy name
    'vorname',  # first name
)
HEADERS_WP_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'gewahlt',  # elected
)
HEADERS_WP_KANDIDATENGDE = (
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


def get_candidate_id(line):
    return str(int(line.knr))


def get_list_id(line):
    if hasattr(line, 'listnr'):
        number = int(line.listnr or 0)
    else:
        number = int(int(get_candidate_id(line)) / 100)
    number = 999 if number == 99 else number  # blank list
    return str(number)


def import_election_wabstic_proporz(
    election, entities, district, number,
    file_wp_wahl, mimetype_wp_wahl,
    file_wpstatic_gemeinden, mimetype_wpstatic_gemeinden,
    file_wp_gemeinden, mimetype_wp_gemeinden,
    file_wp_listen, mimetype_wp_listen,
    file_wp_listengde, mimetype_wp_listengde,
    file_wpstatic_kandidaten, mimetype_wpstatic_kandidaten,
    file_wp_kandidaten, mimetype_wp_kandidaten,
    file_wp_kandidatengde, mimetype_wp_kandidatengde
):
    """ Tries to import the files in the given folder.

    We assume that the files there have been uploaded via FTP using the
    WabstiCExport 2.1.

    """

    errors = []

    # Read the files
    wp_wahl, error = load_csv(
        file_wp_wahl, mimetype_wp_wahl,
        expected_headers=HEADERS_WP_WAHL,
        filename='wp_wahl'
    )
    if error:
        errors.append(error)

    wpstatic_gemeinden, error = load_csv(
        file_wpstatic_gemeinden, mimetype_wpstatic_gemeinden,
        expected_headers=HEADERS_WPSTATIC_GEMEINDEN,
        filename='wpstatic_gemeinden'
    )
    if error:
        errors.append(error)

    wp_gemeinden, error = load_csv(
        file_wp_gemeinden, mimetype_wp_gemeinden,
        expected_headers=HEADERS_WP_GEMEINDEN,
        filename='wp_gemeinden'
    )
    if error:
        errors.append(error)

    wp_listen, error = load_csv(
        file_wp_listen, mimetype_wp_listen,
        expected_headers=HEADERS_WP_LISTEN,
        filename='wp_listen'
    )
    if error:
        errors.append(error)

    wp_listengde, error = load_csv(
        file_wp_listengde, mimetype_wp_listengde,
        expected_headers=HEADERS_WP_LISTENGDE,
        filename='wp_listengde'
    )
    if error:
        errors.append(error)

    wpstatic_kandidaten, error = load_csv(
        file_wpstatic_kandidaten, mimetype_wpstatic_kandidaten,
        expected_headers=HEADERS_WPSTATIC_KANDIDATEN,
        filename='wpstatic_kandidaten'
    )
    if error:
        errors.append(error)

    wp_kandidaten, error = load_csv(
        file_wp_kandidaten, mimetype_wp_kandidaten,
        expected_headers=HEADERS_WP_KANDIDATEN,
        filename='wp_kandidaten'
    )
    if error:
        errors.append(error)

    wp_kandidatengde, error = load_csv(
        file_wp_kandidatengde, mimetype_wp_kandidatengde,
        expected_headers=HEADERS_WP_KANDIDATENGDE,
        filename='wp_kandidatengde'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Parse the election
    complete = 0
    for line in wp_wahl.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            complete = int(line.ausmittlungsstand or 0)
            assert 0 <= complete <= 3
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid values"))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_wahl'
                )
                for err in line_errors
            )
            continue

    # Parse the entities
    added_entities = {}
    for line in wpstatic_gemeinden.lines:
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
                    filename='wpstatic_gemeinden'
                )
                for err in line_errors
            )
            continue

        added_entities[entity_id] = {
            'group': entities.get(entity_id, {}).get('name', ''),
            'elegible_voters': elegible_voters
        }

    for line in wp_gemeinden.lines:
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
                # We can live with this, the static file previously above
                # only contains eligible voters
                added_entities[entity_id] = {
                    'group': entities.get(entity_id, {}).get('name', '')
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
        except ValueError:
            line_errors.append(_("Invalid entity values"))
        else:
            entity['received_ballots'] = received_ballots
            entity['blank_ballots'] = blank_ballots
            entity['invalid_ballots'] = invalid_ballots
            entity['blank_votes'] = 0  # they are in the list results

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_gemeinden'
                )
                for err in line_errors
            )
            continue

    # Parse the lists
    added_lists = {}
    added_connections = {}
    for line in wp_listen.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            list_id = get_list_id(line)
            name = line.listcode
            number_of_mandates = int(line.sitze or 0)
            connection = line.listverb or None
            subconnection = line.listuntverb or None
            if subconnection:
                assert connection
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid list values"))
        else:
            if list_id in added_lists:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': list_id}))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_listen')
                for err in line_errors
            )
            continue

        connection_id = None
        if connection:
            parent_id = None
            if subconnection:
                parent_id = added_connections.setdefault(
                    (connection, None),
                    ListConnection(id=uuid4(), connection_id=connection)
                ).id

            connection_id = added_connections.setdefault(
                (connection, subconnection),
                ListConnection(
                    id=uuid4(),
                    parent_id=parent_id,
                    connection_id=subconnection or connection,
                )
            ).id

        added_lists[list_id] = List(
            id=uuid4(),
            list_id=list_id,
            name=name,
            number_of_mandates=number_of_mandates,
            connection_id=connection_id
        )

    # Parse the list results
    added_list_results = {}
    for line in wp_listengde.lines:
        line_errors = []

        # Why is there no Sort Geschaeft?
        # if not line_is_relevant(line, number):
        #     continue

        try:
            entity_id = get_entity_id(line, entities)
            list_id = get_list_id(line)
            votes = int(line.stimmentotal)
        except ValueError:
            line_errors.append(_("Invalid list results"))
        else:
            if entity_id not in added_entities:
                line_errors.append(_("Invalid entity values"))

            if list_id in added_list_results.get(entity_id, {}):
                line_errors.append(
                    _(
                        "${name} was found twice",
                        mapping={
                            'name': '{}/{}'.format(entity_id, list_id)
                        }
                    )
                )

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_listengde')
                for err in line_errors
            )
            continue

        if list_id == '999':
            added_entities[entity_id]['blank_votes'] = votes

        if entity_id not in added_list_results:
            added_list_results[entity_id] = {}
        added_list_results[entity_id][list_id] = votes

    # Parse the candidates
    added_candidates = {}
    for line in wpstatic_kandidaten.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = get_candidate_id(line)
            list_id = get_list_id(line)
            family_name = line.nachname
            first_name = line.vorname
        except ValueError:
            line_errors.append(_("Invalid candidate values"))
        else:
            if candidate_id in added_candidates:
                line_errors.append(
                    _("${name} was found twice",
                      mapping={'name': candidate_id}))

            if list_id not in added_lists:
                line_errors.append(_("Invalid list values"))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wpstatic_kandidaten'
                )
                for err in line_errors
            )
            continue

        added_candidates[candidate_id] = Candidate(
            id=uuid4(),
            candidate_id=candidate_id,
            family_name=family_name,
            first_name=first_name,
            list_id=added_lists[list_id].id
        )

    for line in wp_kandidaten.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = get_candidate_id(line)
            assert candidate_id in added_candidates
            elected = True if line.gewahlt == '1' else False
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid candidate values"))
        else:
            added_candidates[candidate_id].elected = elected

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wpstatic_kandidaten'
                )
                for err in line_errors
            )
            continue

    added_results = {}
    for line in wp_kandidatengde.lines:
        line_errors = []

        # Why is there no Sort Geschaeft?
        # if not line_is_relevant(line, number):
        #     continue

        try:
            entity_id = get_entity_id(line, entities)
            candidate_id = get_candidate_id(line)
            assert candidate_id in added_candidates
            votes = int(line.stimmen)
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid candidate results"))
        else:
            if entity_id not in added_entities:
                line_errors.append(_("Invalid entity values"))

            if candidate_id in added_results.get(entity_id, {}):
                line_errors.append(
                    _(
                        "${name} was found twice",
                        mapping={
                            'name': '{}/{}'.format(entity_id, candidate_id)
                        }
                    )
                )

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wp_kandidatengde'
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

        election.counted_entities = sum([
            1 for value in added_entities.values() if value['counted']
        ])
        election.total_entities = max(len(entities), len(added_results.keys()))
        election.status = 'unknown'
        if complete == 1:
            election.status = 'interim'
        if complete == 2:
            election.status = 'final'

        for key in filter(lambda x: not x[1], added_connections.keys()):
            election.list_connections.append(added_connections[key])
        for key in filter(lambda x: x[1], added_connections.keys()):
            election.list_connections.append(added_connections[key])

        for list_id, list_ in added_lists.items():
            if list_id != '999':
                election.lists.append(list_)

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
            )
            for candidate_id, votes in added_results[entity_id].items():
                result.candidate_results.append(
                    CandidateResult(
                        votes=votes,
                        candidate_id=added_candidates[candidate_id].id
                    )
                )

            for list_id, votes in added_list_results[entity_id].items():
                if list_id != '999':
                    result.list_results.append(ListResult(
                        votes=votes,
                        list_id=added_lists[list_id].id
                    ))
            election.results.append(result)

    return []
