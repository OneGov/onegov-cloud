from onegov.ballot import (
    Candidate,
    CandidateResult,
    ElectionResult,
    List,
    ListConnection,
    ListResult
)
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv
from sqlalchemy.orm import object_session
from uuid import uuid4


HEADERS = [
    # Municipality
    'Einheit_BFS',
    # Candidate
    'Liste_KandID',
    'Kand_Nachname',
    'Kand_Vorname',
    # List
    'Liste_ID',
    'Liste_Code',
    'Kand_StimmenTotal',
    'Liste_ParteistimmenTotal',
]

HEADERS_CONNECTIONS = [
    'Liste',
    'LV',
    'LUV',
]

HEADERS_RESULT = [
    'ID',
]

HEADERS_STATS = [
    'Einheit_BFS',
    'StimBerTotal',
    'WZEingegangen',
    'WZLeer',
    'WZUngueltig',
    'StmWZVeraendertLeerAmtlLeer',
]


def parse_election_result(line, errors, municipalities):
    try:
        entity_id = int(line.einheit_bfs or 0)
    except ValueError:
        errors.append(_("Invalid municipality values"))
    else:
        if entity_id not in municipalities:
            errors.append(_(
                "municipality id ${id} is unknown",
                mapping={'id': entity_id}
            ))
        else:
            return ElectionResult(
                id=uuid4(),
                group=municipalities[entity_id]['name'],
                entity_id=entity_id,
            )


def parse_list(line, errors):
    try:
        id = int(line.liste_id or 0)
        name = line.liste_code
    except ValueError:
        errors.append(_("Invalid list values"))
    else:
        return List(
            id=uuid4(),
            list_id=id,
            number_of_mandates=0,
            name=name,
        )


def parse_list_result(line, errors):
    try:
        votes = int(line.liste_parteistimmentotal or 0)
    except ValueError:
        errors.append(_("Invalid list results"))
    else:
        return ListResult(
            id=uuid4(),
            votes=votes
        )


def parse_candidate(line, errors):
    try:
        id = int(line.liste_kandid or 0)
        family_name = line.kand_nachname
        first_name = line.kand_vorname
    except ValueError:
        errors.append(_("Invalid candidate values"))
    else:
        return Candidate(
            id=uuid4(),
            candidate_id=id,
            family_name=family_name,
            first_name=first_name,
            elected=False
        )


def parse_candidate_result(line, errors):
    try:
        votes = int(line.kand_stimmentotal or 0)
    except ValueError:
        errors.append(_("Invalid candidate results"))
    else:
        return CandidateResult(
            id=uuid4(),
            votes=votes,
        )


def parse_connection(line, errors):
    try:
        id = int(line.liste or 0)
        connection_id = line.lv
        subconnection_id = line.luv
    except ValueError:
        errors.append(_("Invalid list connection values"))
    else:
        connection = ListConnection(
            id=uuid4(),
            connection_id=connection_id,
        ) if connection_id else None
        subconnection = ListConnection(
            id=uuid4(),
            connection_id=subconnection_id,
        ) if subconnection_id else None
        return id, connection, subconnection


def import_file(municipalities, election, file, mimetype,
                connections_file=None,
                connections_mimetype=None,
                elected_file=None, elected_mimetype=None,
                statistics_file=None, statistics_mimetype=None):
    errors = []
    candidates = {}
    lists = {}
    list_results = {}
    connections = {}
    subconnections = {}
    results = {}

    # This format has one candiate per municipality per line
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS
    )
    if error:
        errors.append(error)
    else:
        for line in csv.lines:
            line_errors = []

            # Parse the line
            result = parse_election_result(line, line_errors, municipalities)
            candidate = parse_candidate(line, line_errors)
            candidate_result = parse_candidate_result(line, line_errors)
            list = parse_list(line, line_errors)
            list_result = parse_list_result(line, line_errors)

            # Pass the errors and continue to next line
            if line_errors:
                errors.extend(
                    FileImportError(error=err, line=line.rownumber)
                    for err in line_errors
                )
                continue

            # Add the data
            result = results.setdefault(result.entity_id, result)

            list = lists.setdefault(list.list_id, list)

            list_results.setdefault(result.entity_id, {})
            list_result = list_results[result.entity_id].setdefault(
                list.list_id, list_result
            )
            list_result.list_id = list.id

            candidate = candidates.setdefault(candidate.candidate_id,
                                              candidate)
            candidate_result.candidate_id = candidate.id
            result.candidate_results.append(candidate_result)

            candidate.list_id = list.id

    # The list connections has one list per line
    if connections_file and connections_mimetype:
        csv, error = load_csv(
            connections_file, connections_mimetype,
            expected_headers=HEADERS_CONNECTIONS
        )
        if error:
            errors.append(error)
        else:
            indexes = dict([(item.id, key) for key, item in lists.items()])
            for line in csv.lines:
                line_errors = []
                id, connection, subconnection = parse_connection(line,
                                                                 line_errors)

                if id not in lists:
                    continue

                if line_errors:
                    errors.extend(
                        FileImportError(error=err, line=line.rownumber)
                        for err in line_errors
                    )
                    continue

                if connection:
                    connection = connections.setdefault(
                        connection.connection_id, connection
                    )
                    lists[id].connection_id = connection.id
                    if subconnection:
                        subconnection = subconnections.setdefault(
                            subconnection.connection_id, subconnection
                        )
                        subconnection.parent_id = connection.id
                        lists[id].connection_id = subconnection.id

    # The results file has one elected candidate per line
    if elected_file and elected_mimetype:
        csv, error = load_csv(
            elected_file, elected_mimetype, expected_headers=HEADERS_RESULT
        )
        if error:
            errors.append(error)
        else:
            indexes = dict([(item.id, key) for key, item in lists.items()])
            for line in csv.lines:
                try:
                    id = int(line.id or 0)
                except ValueError:
                    errors.append(
                        FileImportError(
                            error=_("Invalid values"),
                            line=line.rownumber
                        )
                    )
                else:
                    if id in candidates:
                        candidates[id].elected = True
                        index = indexes[candidates[id].list_id]
                        lists[index].number_of_mandates = 1 + \
                            lists[index].number_of_mandates
                    else:
                        errors.append(
                            FileImportError(
                                error=_("Unknown candidate"),
                                line=line.rownumber
                            )
                        )

    # The stats file has one muncipality per line
    if statistics_file and statistics_mimetype:
        csv, error = load_csv(
            statistics_file, statistics_mimetype,
            expected_headers=HEADERS_STATS
        )
        if error:
            errors.append(error)
        else:
            for line in csv.lines:
                try:
                    id = int(line.einheit_bfs or 0)
                    elegible_voters = int(line.stimbertotal or 0)
                    received_ballots = int(line.wzeingegangen or 0)
                    blank_ballots = int(line.wzleer or 0)
                    invalid_ballots = int(line.wzungueltig or 0)
                    blank_votes = int(line.stmwzveraendertleeramtlleer or 0)
                except ValueError:
                    errors.append(
                        FileImportError(
                            error=_("Invalid values"),
                            line=line.rownumber
                        )
                    )
                else:
                    if id in results:
                        results[id].elegible_voters = elegible_voters
                        results[id].received_ballots = received_ballots
                        results[id].blank_ballots = blank_ballots
                        results[id].invalid_ballots = invalid_ballots
                        results[id].blank_votes = blank_votes

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return {'status': 'error', 'errors': errors}

    if results:
        election.counted_entities = len(results)
        election.total_entities = 0

        session = object_session(election)

        for connection in election.list_connections:
            session.delete(connection)
        for connection in connections.values():
            election.list_connections.append(connection)
        for connection in subconnections.values():
            election.list_connections.append(connection)

        for list in election.lists:
            session.delete(list)
        for list in lists.values():
            election.lists.append(list)

        for candidate in election.candidates:
            session.delete(candidate)
        for candidate in candidates.values():
            election.candidates.append(candidate)

        for result in election.results:
            session.delete(result)
        for result in results.values():
            id = result.entity_id
            for list_result in list_results.get(id, {}).values():
                result.list_results.append(list_result)
            election.results.append(result)

    return {'status': 'ok', 'errors': errors}
