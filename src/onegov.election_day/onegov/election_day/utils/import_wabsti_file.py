from onegov.ballot import (
    Candidate,
    CandidateResult,
    ElectionResult,
    List,
    ListConnection,
    ListResult
)
from onegov.election_day import _
from onegov.election_day.utils import FileImportError, load_csv
from sqlalchemy.orm import object_session
from uuid import uuid4


HEADERS_COMMON = [
    # Municipality
    'AnzMandate',
    'BFS',
    'StimmBer',
    'StimmAbgegeben',
    'StimmLeer',
    'StimmUngueltig',
    'StimmGueltig',
]

HEADERS_MAJORZ = [
]

HEADERS_PROPORZ = [
]


def parse_election(line, errors):
    try:
        mandates = int(line.anzmandate or 0)
        # todo: we are missing this informations
        counted = 0
        total = 1
    except ValueError:
        errors.append(_("Invalid election values"))
    else:
        return mandates, counted, total


def parse_election_result(line, errors, municipalities):
    try:
        municipality_id = int(line.bfs or 0)
        elegible_voters = int(line.stimmber or 0)
        received_ballots = int(line.stimmabgegeben or 0)
        blank_ballots = int(line.stimmleer or 0)
        invalid_ballots = int(line.stimmungueltig or 0)

        blank_votes = None
        invalid_votes = None
        count = 0
        while True:
            count += 1
            try:
                name = getattr(line, 'kandname_{}'.format(count))
                votes = int(getattr(line, 'stimmen_{}'.format(count)) or 0)
            except AttributeError:
                break
            except:
                raise
            else:
                if name == 'Leere Zeilen':
                    blank_votes = votes
                elif name == 'Ungültige Stimmen':
                    invalid_votes = votes

        if not elegible_voters or blank_votes is None or invalid_votes is None:
            raise ValueError()

    except ValueError:
        errors.append(_("Invalid muncipality values"))
    else:
        if municipality_id not in municipalities:
            errors.append(_(
                "municipality id ${id} is unknown",
                mapping={'id': municipality_id}
            ))
        else:
            return ElectionResult(
                id=uuid4(),
                group=municipalities[municipality_id]['name'],
                municipality_id=municipality_id,
                elegible_voters=elegible_voters,
                received_ballots=received_ballots,
                blank_ballots=blank_ballots,
                invalid_ballots=invalid_ballots,
                blank_votes=blank_votes,
                invalid_votes=invalid_votes,
            )

# def parse_list(line, errors):
#     try:
#         id = int(line.listen_nr or 0)
#         name = line.parteibezeichnung
#         mandates = int(line.anzahl_sitze_liste or 0)
#     except ValueError:
#         errors.append(_("Invalid list values"))
#     else:
#         return List(
#             id=uuid4(),
#             list_id=id,
#             number_of_mandates=mandates,
#             name=name,
#         )
#
#
# def parse_list_result(line, errors):
#     try:
#         votes = (
#             int(line.kandidatenstimmen_unveranderte_wahlzettel or 0) +
#             int(line.kandidatenstimmen_veranderte_wahlzettel or 0) +
#             int(line.zusatzstimmen_unveranderte_wahlzettel or 0) +
#             int(line.zusatzstimmen_veranderte_wahlzettel or 0)
#         )
#     except ValueError:
#         errors.append(_("Invalid list results"))
#     else:
#         return ListResult(
#             id=uuid4(),
#             votes=votes
#         )


def parse_candidates(line, errors):
    results = []
    index = 0
    while True:
        index += 1
        try:
            id = getattr(line, 'kandid_{}'.format(index))
            family_name = getattr(line, 'kandname_{}'.format(index))
            first_name = getattr(line, 'kandvorname_{}'.format(index))
            elected = False  # todo: we are missing this information
            votes = int(getattr(line, 'stimmen_{}'.format(index)) or 0)
        except AttributeError:
            break
        except ValueError:
            errors.append(_("Invalid candidate values"))
            break
        else:
            skip = ('Vereinzelte',  'Leere Zeilen', 'Ungültige Stimmen')
            if family_name in skip:
                continue
            results.append((
                Candidate(
                    id=uuid4(),
                    candidate_id=id,
                    family_name=family_name,
                    first_name=first_name,
                    elected=elected
                ),
                CandidateResult(
                    id=uuid4(),
                    votes=votes,
                )
            ))
    return results


# def parse_candidate(line, index, errors):
#     try:
#         id = getattr(line, 'kandid_{}'.format(index))
#         family_name = getattr(line, 'kandname_{}'.format(index))
#         first_name = getattr(line, 'kandvorname_{}'.format(index))
#         # todo: we are missing this information
#         elected = False
#     except AttributeError:
#         return None
#     except ValueError:
#         errors.append(_("Invalid candidate values"))
#     else:
#         return Candidate(
#             id=uuid4(),
#             candidate_id=id,
#             family_name=family_name,
#             first_name=first_name,
#             elected=elected
#         )
#
#
# def parse_candidate_result(line, index, errors):
#     try:
#         votes = int(getattr(line, 'stimmen_{}'.format(index)) or 0)
#     except AttributeError:
#         return None
#     except ValueError:
#         errors.append(_("Invalid candidate results"))
#     else:
#         return CandidateResult(
#             id=uuid4(),
#             votes=votes,
#         )


# def parse_connection(line, errors):
#     try:
#         connection_id = line.hlv_nr
#         subconnection_id = line.ulv_nr
#     except ValueError:
#         errors.append(_("Invalid list connection values"))
#     else:
#         connection = ListConnection(
#             id=uuid4(),
#             connection_id=connection_id,
#         ) if connection_id else None
#         subconnection = ListConnection(
#             id=uuid4(),
#             connection_id=subconnection_id,
#         ) if subconnection_id else None
#         return connection, subconnection

def import_file(municipalities, election, file, mimetype):
    majorz = True
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_MAJORZ
    )
    # majorz = False
    # csv, error = load_csv(
    #     file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_PROPORZ
    # )
    # if error and "Missing columns" in error.error:
    #     majorz = True
    #     csv, error = load_csv(
    #         file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_MAJORZ
    #     )
    # type_matches = (
    #     (majorz and election.type == 'majorz') or
    #     (not majorz and election.type == 'proporz')
    # )
    # if not type_matches:
    #     error = FileImportError(_(
    #         "The type of the file does not match the type of the election."
    #     ))
    # if error:
    #     return {'status': 'error', 'errors': [error]}

    errors = []

    candidates = {}
    lists = {}
    list_results = {}
    connections = {}
    subconnections = {}
    results = []

    # This format has one municipality per line and every candidate as row
    mandates = 0
    counted = 0
    total = 0
    for line in csv.lines:
        line_errors = []

        # Parse the line
        mandates, counted, total = parse_election(line, line_errors)
        result = parse_election_result(line, line_errors, municipalities)
        for candidate, candidate_result in parse_candidates(line, line_errors):
            # proporz: might be that the list value is wrong at this time?
            candidate = candidates.setdefault(
                candidate.candidate_id, candidate
            )
            candidate_result.candidate_id = candidate.id
            result.candidate_results.append(candidate_result)
        # while True:
        #     index += 1
        #     candidate = parse_candidate(line, index, line_errors)
        #     candidate_result = parse_candidate_result(line, index, line_errors)
        #     if not candidate or not candidate_result:
        #         break
        #     # proporz: might be that the list value is wrong at this time?
        #     candidate = candidates.setdefault(
        #         candidate.candidate_id, candidate
        #     )
        #     candidate_result.candidate_id = candidate.id
        #     result.candidate_results.append(candidate_result)

        # if not majorz:
        #     list = parse_list(line, line_errors)
        #     list_result = parse_list_result(line, line_errors)
        #     connection, subconnection = parse_connection(line, line_errors)

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        results.append(result)
        # if not majorz:
        #     list = lists.setdefault(list.list_id, list)
        #
        #     if connection:
        #         connection = connections.setdefault(
        #             connection.connection_id, connection
        #         )
        #         list.connection_id = connection.id
        #         if subconnection:
        #             subconnection = subconnections.setdefault(
        #                 subconnection.connection_id, subconnection
        #             )
        #             subconnection.parent_id = connection.id
        #             list.connection_id = subconnection.id
        #
        #     list_results.setdefault(result.municipality_id, {})
        #     list_result = list_results[result.municipality_id].setdefault(
        #         list.list_id, list_result
        #     )
        #     list_result.list_id = list.id

        # if not majorz:
        #     candidate.list_id = list.id

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return {'status': 'error', 'errors': errors}

    if results:
        election.number_of_mandates = mandates
        election.counted_municipalities = counted
        election.total_municipalities = total

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
        for result in results:
            id = result.municipality_id
            for list_result in list_results.get(id, {}).values():
                result.list_results.append(list_result)
            election.results.append(result)

    return {'status': 'ok', 'errors': errors}
