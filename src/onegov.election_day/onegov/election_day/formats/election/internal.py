from csv import excel
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import PanachageResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import STATI
from uuid import uuid4


HEADERS = [
    'election_absolute_majority',
    'election_status',
    'election_counted_entities',
    'election_total_entities',
    'entity_id',
    'entity_name',
    'entity_elegible_voters',
    'entity_received_ballots',
    'entity_blank_ballots',
    'entity_invalid_ballots',
    'entity_blank_votes',
    'entity_invalid_votes',
    'list_name',
    'list_id',
    'list_number_of_mandates',
    'list_votes',
    'list_connection',
    'list_connection_parent',
    'candidate_family_name',
    'candidate_first_name',
    'candidate_id',
    'candidate_elected',
    'candidate_votes',
    'candidate_party',
]


def parse_election(line, errors):
    counted = 0
    total = 0
    majority = None
    status = None
    try:
        if line.election_absolute_majority:
            majority = int(line.election_absolute_majority or 0)
            majority = majority if majority else None
        counted = int(line.election_counted_entities or 0)
        total = int(line.election_total_entities or 0)
        status = line.election_status or 'unknown'
    except ValueError:
        errors.append(_("Invalid election values"))
    if status not in STATI:
        errors.append(_("Invalid status"))
    return counted, total, majority, status


def parse_election_result(line, errors, entities):
    try:
        group = line.entity_name.strip()
        entity_id = int(line.entity_id or 0)
        elegible_voters = int(line.entity_elegible_voters or 0)
        received_ballots = int(line.entity_received_ballots or 0)
        blank_ballots = int(line.entity_blank_ballots or 0)
        invalid_ballots = int(line.entity_invalid_ballots or 0)
        blank_votes = int(line.entity_blank_votes or 0)
        invalid_votes = int(line.entity_invalid_votes or 0)

        if not elegible_voters:
            raise ValueError()

    except ValueError:
        errors.append(_("Invalid entity values"))
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
            errors.append(_(
                "${name} is unknown",
                mapping={'name': entity_id}
            ))
        else:
            return ElectionResult(
                id=uuid4(),
                group=group,
                entity_id=entity_id,
                elegible_voters=elegible_voters,
                received_ballots=received_ballots,
                blank_ballots=blank_ballots,
                invalid_ballots=invalid_ballots,
                blank_votes=blank_votes,
                invalid_votes=invalid_votes,
            )


def parse_list(line, errors):
    try:
        id = int(line.list_id or 0)
        name = line.list_name
        mandates = int(line.list_number_of_mandates or 0)
    except ValueError:
        errors.append(_("Invalid list values"))
    else:
        return List(
            id=uuid4(),
            list_id=id,
            number_of_mandates=mandates,
            name=name,
        )


def parse_list_result(line, errors):
    try:
        votes = int(line.list_votes or 0)
    except ValueError:
        errors.append(_("Invalid list results"))
    else:
        return ListResult(
            id=uuid4(),
            votes=votes
        )


def parse_panachage_headers(csv):
    headers = {}
    for header in csv.headers:
        if header.startswith('panachage_votes_from_list_'):
            parts = header.split('panachage_votes_from_list_')
            if len(parts) > 1:
                try:
                    number = int(parts[1])
                    headers[csv.as_valid_identifier(header)] = number
                except ValueError:
                    pass
    return headers


def parse_panachage_results(line, errors, panachage):
    try:
        target = int(line.list_id or 0)
        if target not in panachage:
            panachage[target] = {}
            for name, index in panachage['headers'].items():
                panachage[target][index] = int(getattr(line, name))

    except ValueError:
        errors.append(_("Invalid list results"))


def parse_candidate(line, errors):
    try:
        id = int(line.candidate_id or 0)
        family_name = line.candidate_family_name
        first_name = line.candidate_first_name
        elected = line.candidate_elected == 'True'
        party = line.candidate_party

    except ValueError:
        errors.append(_("Invalid candidate values"))
    else:
        return Candidate(
            id=uuid4(),
            candidate_id=id,
            family_name=family_name,
            first_name=first_name,
            elected=elected,
            party=party
        )


def parse_candidate_result(line, errors):
    try:
        votes = int(line.candidate_votes or 0)
    except ValueError:
        errors.append(_("Invalid candidate results"))
    else:
        return CandidateResult(
            id=uuid4(),
            votes=votes,
        )


def parse_connection(line, errors):
    subconnection_id = None
    try:
        connection_id = line.list_connection
        parent_connection_id = line.list_connection_parent
        if parent_connection_id:
            subconnection_id = connection_id
            connection_id = parent_connection_id
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
        return connection, subconnection


def import_election_internal(election, entities, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.Election.export().

    :return:
        A list containing errors.

    """
    filename = _("Results")
    majorz = election.type == 'majorz'
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename,
        dialect=excel
    )
    if error:
        return [error]

    errors = []

    candidates = {}
    lists = {}
    list_results = {}
    connections = {}
    subconnections = {}
    results = {}
    panachage = {'headers': parse_panachage_headers(csv)}

    # This format has one candiate per entity per line
    counted = 0
    total = 0
    absolute_majority = None
    status = None
    for line in csv.lines:
        line_errors = []

        # Parse the line
        counted, total, absolute_majority, status = parse_election(
            line, line_errors
        )
        result = parse_election_result(line, line_errors, entities)
        candidate = parse_candidate(line, line_errors)
        candidate_result = parse_candidate_result(line, line_errors)
        if not majorz:
            list_ = parse_list(line, line_errors)
            list_result = parse_list_result(line, line_errors)
            connection, subconnection = parse_connection(line, line_errors)
            parse_panachage_results(line, line_errors, panachage)

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
        result = results.setdefault(result.entity_id, result)

        if not majorz:
            list_ = lists.setdefault(list_.list_id, list_)

            if connection:
                connection = connections.setdefault(
                    connection.connection_id, connection
                )
                list_.connection_id = connection.id
                if subconnection:
                    subconnection = subconnections.setdefault(
                        subconnection.connection_id, subconnection
                    )
                    subconnection.parent_id = connection.id
                    list_.connection_id = subconnection.id

            list_results.setdefault(result.entity_id, {})
            list_result = list_results[result.entity_id].setdefault(
                list_.list_id, list_result
            )
            list_result.list_id = list_.id

        candidate = candidates.setdefault(candidate.candidate_id, candidate)
        candidate_result.candidate_id = candidate.id
        result.candidate_results.append(candidate_result)

        if not majorz:
            candidate.list_id = list_.id

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return errors

    if results:
        election.clear_results()

        if absolute_majority is not None:
            election.absolute_majority = absolute_majority
        election.status = status
        election.counted_entities = counted
        election.total_entities = total

        for connection in connections.values():
            election.list_connections.append(connection)
        for connection in subconnections.values():
            election.list_connections.append(connection)

        for list_ in lists.values():
            election.lists.append(list_)
            if list_.list_id in panachage:
                for source, votes in panachage[list_.list_id].items():
                    list_.panachage_results.append(
                        PanachageResult(source_list_id=source, votes=votes)
                    )

        for candidate in candidates.values():
            election.candidates.append(candidate)

        for result in results.values():
            id = result.entity_id
            for list_result in list_results.get(id, {}).values():
                result.list_results.append(list_result)
            election.results.append(result)

    return []
