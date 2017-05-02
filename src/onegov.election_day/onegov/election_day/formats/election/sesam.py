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
from onegov.election_day.utils import clear_election
from uuid import uuid4


HEADERS_COMMON = [
    # Entity
    'Anzahl Sitze',
    'Wahlkreis-Nr',
    'Wahlkreisbezeichnung',
    'Stimmberechtigte',
    'Wahlzettel',
    'Ungültige Wahlzettel',
    'Leere Wahlzettel',
    'Leere Stimmen',
    # Candidate
    'Kandidaten-Nr',
    'Name',
    'Vorname',
    # Election
    'Anzahl Gemeinden',
]

HEADERS_MAJORZ = [
    # Entity
    'Ungueltige Stimmen',
    # Candidate
    'Stimmen',
]

HEADERS_PROPORZ = [
    # List
    'Listen-Nr',
    'Parteibezeichnung',
    'HLV-Nr',
    'ULV-Nr',
    'Anzahl Sitze Liste',
    'Kandidatenstimmen unveränderte Wahlzettel',
    'Zusatzstimmen unveränderte Wahlzettel',
    'Kandidatenstimmen veränderte Wahlzettel',
    'Zusatzstimmen veränderte Wahlzettel',
    # Candidate
    'Gewählt',
    'Stimmen Total aus Wahlzettel',
]


def parse_election(line, errors):
    mandates = 0
    counted = 0
    total = 0
    try:
        mandates = int(line.anzahl_sitze or 0)
        numbers = line.anzahl_gemeinden.split(' von ')
        if not len(numbers) == 2:
            raise ValueError()
        else:
            counted = int(numbers[0])
            total = int(numbers[1])
    except ValueError:
        errors.append(_("Invalid election values"))
    return mandates, counted, total


def parse_election_result(line, errors, entities):
    try:
        group = line.wahlkreisbezeichnung.strip()
        entity_id = int(line.wahlkreis_nr or 0)
        elegible_voters = int(line.stimmberechtigte or 0)
        received_ballots = int(line.wahlzettel or 0)
        blank_ballots = int(line.leere_wahlzettel or 0)
        invalid_ballots = int(line.ungultige_wahlzettel or 0)
        blank_votes = int(line.leere_stimmen or 0)

        if not elegible_voters:
            raise ValueError()

        try:
            invalid_votes = int(line.ungueltige_stimmen or 0)  # majorz
        except AttributeError:
            invalid_votes = 0  # proporz
    except ValueError:
        errors.append(_("Invalid entity values"))
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
            errors.append(_(
                _("${name} is unknown", mapping={'name': entity_id})
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
        id = int(line.listen_nr or 0)
        name = line.parteibezeichnung
        mandates = int(line.anzahl_sitze_liste or 0)
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
        votes = (
            int(line.kandidatenstimmen_unveranderte_wahlzettel or 0) +
            int(line.kandidatenstimmen_veranderte_wahlzettel or 0) +
            int(line.zusatzstimmen_unveranderte_wahlzettel or 0) +
            int(line.zusatzstimmen_veranderte_wahlzettel or 0)
        )
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
        if header[0] and header[0] in '0123456789':
            parts = header.split(' ')
            if len(parts) > 1:
                try:
                    number = int(parts[0])
                    number = 999 if number == 0 else number  # blank list
                    headers[csv.as_valid_identifier(header)] = number
                except ValueError:
                    pass
    return headers


def parse_panachage_results(line, errors, panachage):
    # Each line (candidate) contains a column for each list from where this
    # candidate got votes. The column with the own list doesn't contain the
    # votes. The name of the columns are '{Listen-Nr} {Parteikurzbezeichnung}'

    try:
        target = int(line.listen_nr or 0)
        if target not in panachage:
            panachage[target] = {}

        for name, index in panachage['headers'].items():
            if index not in panachage[target]:
                panachage[target][index] = 0
            panachage[target][index] += int(getattr(line, name))

    except ValueError:
        errors.append(_("Invalid list results"))


def parse_candidate(line, errors):
    try:
        id = int(line.kandidaten_nr or 0)
        family_name = line.name
        first_name = line.vorname
        try:
            elected = line.gewaehlt == 'Gewaehlt'
        except AttributeError:
            elected = line.gewahlt == 'Gewählt'
    except ValueError:
        errors.append(_("Invalid candidate values"))
    else:
        return Candidate(
            id=uuid4(),
            candidate_id=id,
            family_name=family_name,
            first_name=first_name,
            elected=elected
        )


def parse_candidate_result(line, errors):
    try:
        try:
            votes = int(line.stimmen or 0)  # majorz
        except AttributeError:
            votes = int(line.stimmen_total_aus_wahlzettel or 0)  # proporz
    except ValueError:
        errors.append(_("Invalid candidate results"))
    else:
        return CandidateResult(
            id=uuid4(),
            votes=votes,
        )


def parse_connection(line, errors):
    try:
        connection_id = line.hlv_nr
        subconnection_id = line.ulv_nr
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


def import_election_sesam(entities, election, file, mimetype):
    """ Tries to import the given file (sesam format).

    :return:
        A list containing errors.

    """
    majorz = election.type == 'majorz'
    filename = _("Results")
    if majorz:
        csv, error = load_csv(
            file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_MAJORZ,
            filename=filename
        )
    else:
        csv, error = load_csv(
            file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_PROPORZ,
            filename=filename
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
    mandates = 0
    counted = 0
    total = 0
    for line in csv.lines:
        line_errors = []

        # Parse the line
        mandates, counted, total = parse_election(line, line_errors)
        result = parse_election_result(line, line_errors, entities)
        candidate = parse_candidate(line, line_errors)
        candidate_result = parse_candidate_result(line, line_errors)
        if not majorz:
            list = parse_list(line, line_errors)
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
            list = lists.setdefault(list.list_id, list)

            if connection:
                connection = connections.setdefault(
                    connection.connection_id, connection
                )
                list.connection_id = connection.id
                if subconnection:
                    subconnection = subconnections.setdefault(
                        subconnection.connection_id, subconnection
                    )
                    subconnection.parent_id = connection.id
                    list.connection_id = subconnection.id

            list_results.setdefault(result.entity_id, {})
            list_result = list_results[result.entity_id].setdefault(
                list.list_id, list_result
            )
            list_result.list_id = list.id

        candidate = candidates.setdefault(candidate.candidate_id, candidate)
        candidate_result.candidate_id = candidate.id
        result.candidate_results.append(candidate_result)

        if not majorz:
            candidate.list_id = list.id

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return errors

    if results:
        clear_election(election)

        election.number_of_mandates = mandates
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
