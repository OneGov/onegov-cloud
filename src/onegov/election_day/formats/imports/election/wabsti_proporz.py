from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import ListPanachageResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_integer
from onegov.election_day.formats.imports.common import validate_list_id
from uuid import uuid4


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from builtins import list as _list
    from onegov.ballot.models import ProporzElection
    from onegov.core.csv import DefaultCSVFile
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from uuid import UUID


WABSTI_PROPORZ_HEADERS = (
    'einheit_bfs',
    'liste_kandid',
    'kand_nachname',
    'kand_vorname',
    'liste_id',
    'liste_code',
    'kand_stimmentotal',
    'liste_parteistimmentotal',
)

WABSTI_PROPORZ_HEADERS_CONNECTIONS = (
    'liste',
    'lv',
    'luv',
)

WABSTI_PROPORZ_HEADERS_CANDIDATES = (
    'liste_kandid',
)

WABSTI_PROPORZ_HEADERS_STATS = (
    'einheit_bfs',
    'einheit_name',
    'stimbertotal',
    'wzeingegangen',
    'wzleer',
    'wzungueltig',
    'stmwzveraendertleeramtlleer',
)


def parse_election_result(
    line: 'DefaultRow',
    errors: list[str],
    entities: dict[int, dict[str, str]],
    election: 'ProporzElection',
    principal: 'Canton | Municipality'
) -> ElectionResult | None:

    try:
        entity_id = validate_integer(line, 'einheit_bfs')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
            errors.append(_(
                _("${name} is unknown", mapping={'name': entity_id})
            ))

        else:
            name, district, superregion = get_entity_and_district(
                entity_id, entities, election, principal, errors
            )

            if not errors:
                return ElectionResult(
                    id=uuid4(),
                    name=name,
                    district=district,
                    superregion=superregion,
                    entity_id=entity_id,
                    counted=True
                )
    return None


def parse_list(line: 'DefaultRow', errors: list[str]) -> List | None:
    try:
        list_id = validate_list_id(line, 'liste_id')
        name = line.liste_code
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return List(
            id=uuid4(),
            list_id=list_id,
            number_of_mandates=0,
            name=name,
        )
    return None


def parse_list_result(
    line: 'DefaultRow',
    errors: list[str]
) -> ListResult | None:

    try:
        votes = validate_integer(line, 'liste_parteistimmentotal')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return ListResult(
            id=uuid4(),
            votes=votes
        )
    return None


def parse_panachage_headers(csv: 'DefaultCSVFile') -> dict[str, str]:
    # header should be of sort {List ID}.{List Code}
    headers: dict[str, str] = {}
    for header in csv.headers:
        if not header[0] and not header[0] in '0123456789':
            return headers
        # since 2019, list_nr can be alphanumeric in sg
        parts = header.split('.')
        if len(parts) > 1:
            try:
                list_id = parts[0]
                list_id = '999' if list_id == '99' else list_id  # blank list
                # as_valid_identfier converts eg 01.alg junge to alg_junge
                headers[csv.as_valid_identifier(header)] = list_id
            except ValueError:
                pass
    return headers


def parse_panachage_results(
    line: 'DefaultRow',
    errors: list[str],
    panachage: dict[str, dict[str, int]],
    panachage_headers: dict[str, str]
) -> None:
    # Each line (candidate) contains a column for each list from where this
    # candidate got votes. The column with the own list doesn't contain the
    # votes. The name of the columns are '{Listen-Nr} {Parteikurzbezeichnung}'
    try:
        target = validate_list_id(line, 'liste_id')
        panachage.setdefault(target, {})

        for list_name, source in panachage_headers.items():
            if source == target:
                continue
            panachage[target].setdefault(source, 0)
            # list_name is csv.as_valid_identifier(original_header)
            panachage[target][source] += validate_integer(line, list_name)

    except ValueError as e:
        errors.append(e.args[0])

    except Exception:
        errors.append(_("Invalid list results"))


def parse_candidate(line: 'DefaultRow', errors: list[str]) -> Candidate | None:
    try:
        candidate_id = validate_integer(line, 'liste_kandid')
        family_name = line.kand_nachname
        first_name = line.kand_vorname

    except ValueError as e:
        errors.append(e.args[0])

    except Exception:
        errors.append(_("Invalid candidate values"))
    else:
        return Candidate(
            id=uuid4(),
            candidate_id=str(candidate_id),
            family_name=family_name,
            first_name=first_name,
            elected=False
        )
    return None


def parse_candidate_result(
    line: 'DefaultRow',
    errors: list[str]
) -> CandidateResult | None:

    try:
        votes = validate_integer(line, 'kand_stimmentotal')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return CandidateResult(
            id=uuid4(),
            votes=votes,
        )
    return None


def parse_connection(
    line: 'DefaultRow',
    errors: list[str]
) -> tuple[str | None, ListConnection | None, ListConnection | None]:

    try:
        list_id = validate_list_id(line, 'liste')
        connection_id = line.lv
        subconnection_id = line.luv

    except ValueError as e:
        errors.append(e.args[0])

    except Exception:
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
        return list_id, connection, subconnection

    return None, None, None


def import_election_wabsti_proporz(
    election: 'ProporzElection',
    principal: 'Canton | Municipality',
    file: IO[bytes],
    mimetype: str,
    connections_file: IO[bytes] | None = None,
    connections_mimetype: str | None = None,
    elected_file: IO[bytes] | None = None,
    elected_mimetype: str | None = None,
    statistics_file: IO[bytes] | None = None,
    statistics_mimetype: str | None = None
) -> list[FileImportError]:
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for proporz elections. Since there is no
    format description, importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """

    errors = []
    candidates: dict[str, Candidate] = {}
    lists: dict[str, List] = {}
    list_results: dict[int, dict[str, ListResult]] = {}
    connections: dict[str, ListConnection] = {}
    subconnections: dict[str, ListConnection] = {}
    results: dict[int, ElectionResult] = {}
    entities = principal.entities[election.date.year]
    panachage_headers = None

    # This format has one candiate per entity per line
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=WABSTI_PROPORZ_HEADERS,
        filename=filename
    )
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype, expected_headers=WABSTI_PROPORZ_HEADERS,
            filename=filename,
            encoding='utf-16-le'
        )
        if utf16_error:
            errors.append(error)
        else:
            error = None
    if not error:
        assert csv is not None
        panachage: dict[str, dict[str, int]] = {}
        panachage_headers = parse_panachage_headers(csv)
        for line in csv.lines:
            line_errors: '_list[str]' = []

            # Parse the line
            result = parse_election_result(
                line, line_errors, entities, election, principal
            )
            candidate = parse_candidate(line, line_errors)
            candidate_result = parse_candidate_result(line, line_errors)
            list = parse_list(line, line_errors)
            list_result = parse_list_result(line, line_errors)
            parse_panachage_results(
                line, line_errors, panachage, panachage_headers)

            # Skip expats if not enabled
            if result and result.entity_id == 0 and not election.has_expats:
                continue

            # Pass the errors and continue to next line
            if line_errors:
                errors.extend(
                    FileImportError(
                        error=err, line=line.rownumber, filename=filename
                    )
                    for err in line_errors
                )
                continue

            # Add the data
            assert result is not None
            result = results.setdefault(result.entity_id, result)

            assert list is not None
            list = lists.setdefault(list.list_id, list)

            assert list_result is not None
            list_results.setdefault(result.entity_id, {})
            list_result = list_results[result.entity_id].setdefault(
                list.list_id, list_result
            )
            list_result.list_id = list.id

            assert candidate is not None
            candidate = candidates.setdefault(candidate.candidate_id,
                                              candidate)
            assert candidate_result is not None
            candidate_result.candidate_id = candidate.id
            result.candidate_results.append(candidate_result)

            candidate.list_id = list.id

    # The list connections has one list per line
    filename = _("List connections")
    if connections_file and connections_mimetype:
        csv, error = load_csv(
            connections_file, connections_mimetype,
            expected_headers=WABSTI_PROPORZ_HEADERS_CONNECTIONS,
            filename=filename
        )
        if error:
            # Wabsti files are sometimes UTF-16
            csv, utf16_error = load_csv(
                connections_file, connections_mimetype,
                expected_headers=WABSTI_PROPORZ_HEADERS_CONNECTIONS,
                filename=filename,
                encoding='utf-16-le'
            )
            if utf16_error:
                errors.append(error)
            else:
                error = None
        if not error:
            assert csv is not None
            for line in csv.lines:
                line_errors = []
                list_id, connection, subconnection = parse_connection(
                    line, line_errors
                )
                if list_id:
                    assert isinstance(list_id, str), 'list_id can be alphanum'
                # Pass the errors and continue to next line
                if line_errors:
                    errors.extend(
                        FileImportError(
                            error=err, line=line.rownumber, filename=filename
                        )
                        for err in line_errors
                    )
                    continue

                if list_id not in lists:
                    continue

                if connection:
                    connection = connections.setdefault(
                        connection.connection_id, connection
                    )
                    lists[list_id].connection_id = connection.id
                    if subconnection:
                        subconnection = subconnections.setdefault(
                            subconnection.connection_id, subconnection
                        )
                        subconnection.parent_id = connection.id
                        lists[list_id].connection_id = subconnection.id

    # The candidates file has one elected candidate per line
    filename = _("Elected Candidates")
    if elected_file and elected_mimetype:
        csv, error = load_csv(
            elected_file, elected_mimetype,
            expected_headers=WABSTI_PROPORZ_HEADERS_CANDIDATES,
            filename=filename
        )
        if error:
            # Wabsti files are sometimes UTF-16
            csv, utf16_error = load_csv(
                elected_file, elected_mimetype,
                expected_headers=WABSTI_PROPORZ_HEADERS_CANDIDATES,
                filename=filename,
                encoding='utf-16-le'
            )
            if utf16_error:
                errors.append(error)
            else:
                error = None
        if not error:
            indexes = {item.id: key for key, item in lists.items()}
            assert csv is not None
            for line in csv.lines:
                try:
                    candidate_id = str(validate_integer(line, 'liste_kandid'))
                except ValueError as e:
                    errors.append(
                        FileImportError(
                            error=e.args[0],
                            line=line.rownumber,
                            filename=filename
                        )
                    )
                else:
                    if candidate_id in candidates:
                        candidates[candidate_id].elected = True
                        list_uuid = candidates[candidate_id].list_id
                        assert list_uuid is not None
                        index = indexes[list_uuid]
                        lists[index].number_of_mandates = (
                            1 + lists[index].number_of_mandates)
                    else:
                        errors.append(
                            FileImportError(
                                error=_("Unknown candidate"),
                                line=line.rownumber,
                                filename=filename
                            )
                        )

    # The stats file has one muncipality per line
    filename = _("Election statistics")
    if statistics_file and statistics_mimetype:
        csv, error = load_csv(
            statistics_file, statistics_mimetype,
            expected_headers=WABSTI_PROPORZ_HEADERS_STATS,
            filename=filename
        )
        if error:
            # Wabsti files are sometimes UTF-16
            csv, utf16_error = load_csv(
                statistics_file, statistics_mimetype,
                expected_headers=WABSTI_PROPORZ_HEADERS_STATS,
                filename=filename,
                encoding='utf-16-le'
            )
            if utf16_error:
                errors.append(error)
            else:
                error = None
        if not error:
            assert csv is not None
            for line in csv.lines:
                try:
                    group = line.einheit_name.strip()
                    entity_id = validate_integer(line, 'einheit_bfs')
                    eligible_voters = validate_integer(line, 'stimbertotal')
                    received_ballots = validate_integer(line, 'wzeingegangen')
                    blank_ballots = validate_integer(line, 'wzleer')
                    invalid_ballots = validate_integer(line, 'wzungueltig')
                    blank_votes = validate_integer(
                        line, 'stmwzveraendertleeramtlleer')
                except ValueError as e:
                    errors.append(
                        FileImportError(
                            error=e.args[0],
                            line=line.rownumber,
                            filename=filename
                        )
                    )
                else:
                    if entity_id not in entities and group.lower() == \
                            'auslandschweizer':
                        entity_id = 0

                    if entity_id in results:
                        results[entity_id].eligible_voters = eligible_voters
                        results[entity_id].received_ballots = received_ballots
                        results[entity_id].blank_ballots = blank_ballots
                        results[entity_id].invalid_ballots = invalid_ballots
                        results[entity_id].blank_votes = blank_votes

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if panachage_headers:
        for list_id in panachage_headers.values():
            if not list_id == '999' and list_id not in lists.keys():
                errors.append(FileImportError(
                    _("Panachage results id ${id} not in list_id's",
                      mapping={'id': list_id})))
                break

    if errors:
        return errors

    # Add the missing entities
    remaining = set(entities.keys())
    if election.has_expats:
        remaining.add(0)
    remaining -= set(results.keys())
    for entity_id in remaining:
        name, district, superregion = get_entity_and_district(
            entity_id, entities, election, principal
        )
        if election.domain == 'none':
            continue
        if election.domain == 'municipality':
            if principal.domain != 'municipality':
                if name != election.domain_segment:
                    continue
        if election.domain in ('region', 'district'):
            if district != election.domain_segment:
                continue
        results[entity_id] = ElectionResult(
            id=uuid4(),
            name=name,
            district=district,
            superregion=superregion,
            entity_id=entity_id,
            counted=False
        )

    election.clear_results()
    election.last_result_change = election.timestamp()
    for association in election.associations:
        association.election_compound.last_result_change = (
            election.last_result_change
        )

    for connection in connections.values():
        election.list_connections.append(connection)
    for connection in subconnections.values():
        election.list_connections.append(connection)

    list_ids: dict[str, 'UUID | None']
    list_ids = {list.list_id: list.id for list in lists.values()}
    list_ids['999'] = None
    for list_ in lists.values():
        election.lists.append(list_)
        if list_.list_id in panachage:
            for source, votes in panachage[list_.list_id].items():
                list_.panachage_results.append(
                    ListPanachageResult(
                        source_id=list_ids[source],
                        votes=votes
                    )
                )

    for candidate in candidates.values():
        election.candidates.append(candidate)

    for result in results.values():
        for list_result in list_results.get(result.entity_id, {}).values():
            result.list_results.append(list_result)
        election.results.append(result)

    return []
