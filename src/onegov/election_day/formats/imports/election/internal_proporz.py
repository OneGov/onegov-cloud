from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import STATI
from onegov.election_day.formats.imports.common import validate_color
from onegov.election_day.formats.imports.common import validate_gender
from onegov.election_day.formats.imports.common import validate_integer
from onegov.election_day.formats.imports.common import validate_list_id
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from sqlalchemy.orm import object_session
from uuid import uuid4


from typing import Any
from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.csv import DefaultCSVFile
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Election
    from onegov.election_day.models import Municipality
    from onegov.election_day.types import Status

    # TODO: Define TypedDict for the parsed results, so we can verify
    #       our parser ensures correct types


INTERNAL_PROPORZ_HEADERS = (
    'election_status',
    'entity_id',
    'entity_counted',
    'entity_eligible_voters',
    'entity_received_ballots',
    'entity_blank_ballots',
    'entity_invalid_ballots',
    'entity_blank_votes',
    'entity_invalid_votes',
    'candidate_family_name',
    'candidate_first_name',
    'candidate_id',
    'candidate_elected',
    'candidate_votes',
    'candidate_party',
    'list_name',
    'list_id',
    'list_number_of_mandates',
    'list_votes',
    'list_connection',
    'list_connection_parent',
)


def parse_election(line: DefaultRow, errors: list[str]) -> Status | None:
    status = None
    try:
        status = line.election_status or 'unknown'
    except ValueError:
        errors.append(_('Invalid election values'))
    if status not in STATI:
        errors.append(_('Invalid status'))
    return status  # type:ignore[return-value]


def parse_election_result(
    line: DefaultRow,
    errors: list[str],
    entities: dict[int, dict[str, str]],
    election: Election,
    principal: Canton | Municipality,
    ignore_extra: bool
) -> dict[str, Any] | bool:

    try:
        entity_id = validate_integer(line, 'entity_id')
        counted = line.entity_counted.strip().lower() == 'true'
        eligible_voters = validate_integer(line, 'entity_eligible_voters')
        expats = validate_integer(
            line, 'entity_expats', optional=True, default=None
        )
        received_ballots = validate_integer(line, 'entity_received_ballots')
        blank_ballots = validate_integer(line, 'entity_blank_ballots')
        invalid_ballots = validate_integer(line, 'entity_invalid_ballots')
        blank_votes = validate_integer(line, 'entity_blank_votes')
        invalid_votes = validate_integer(line, 'entity_invalid_votes')

    except ValueError as e:
        errors.append(e.args[0])

    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
            errors.append(_(
                '${name} is unknown',
                mapping={'name': entity_id}
            ))

        else:
            entity_errors: list[str] = []
            name, district, superregion = get_entity_and_district(
                entity_id, entities, election, principal, entity_errors
            )
            if ignore_extra and entity_errors:
                return True
            errors.extend(entity_errors)

            if not errors:
                return {
                    'id': uuid4(),
                    'election_id': election.id,
                    'name': name,
                    'district': district,
                    'superregion': superregion,
                    'counted': counted,
                    'entity_id': entity_id,
                    'eligible_voters': eligible_voters if counted else 0,
                    'expats': expats if counted else 0,
                    'received_ballots': received_ballots if counted else 0,
                    'blank_ballots': blank_ballots if counted else 0,
                    'invalid_ballots': invalid_ballots if counted else 0,
                    'blank_votes': blank_votes if counted else 0,
                    'invalid_votes': invalid_votes if counted else 0,
                }

    return False


def parse_list(
    line: DefaultRow,
    errors: list[str],
    election_id: str,
    colors: dict[str, str]
) -> dict[str, Any] | None:

    try:
        id = validate_list_id(line, 'list_id', treat_empty_as_default=False)
        name = line.list_name
        color = validate_color(line, 'list_color')
        mandates = validate_integer(line, 'list_number_of_mandates')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        if name and color:
            colors[name] = color
        return {
            'id': uuid4(),
            'election_id': election_id,
            'list_id': id,
            'number_of_mandates': mandates,
            'name': name,
        }
    return None


def parse_list_result(
    line: DefaultRow,
    errors: list[str],
    counted: bool
) -> dict[str, Any] | None:

    try:
        votes = validate_integer(line, 'list_votes')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return {
            'id': uuid4(),
            'votes': votes if counted else 0
        }
    return None


def parse_list_panachage_headers(csv: DefaultCSVFile) -> dict[str, str]:
    headers = {}
    prefix = 'list_panachage_votes_from_list_'
    for header in csv.headers:
        if header.startswith('panachage_votes_from_list_'):
            prefix = 'panachage_votes_from_list_'
        if not header.startswith(prefix):
            continue
        parts = header.split(prefix)
        if len(parts) > 1:
            try:
                source_list_id = parts[1]
                headers[csv.as_valid_identifier(header)] = source_list_id
            except ValueError:
                pass
    return headers


def parse_list_panachage_results(
    line: DefaultRow,
    errors: list[str],
    values: dict[str, dict[str, int]],
    headers: dict[str, str]
) -> None:

    try:
        target = validate_list_id(
            line, 'list_id', treat_empty_as_default=False)
        if target not in values:
            values[target] = {}
            for col_name, source in headers.items():
                if source == target:
                    continue
                votes = validate_integer(line, col_name, default=None)
                if votes is not None:
                    values[target][source] = votes

    except ValueError as e:
        errors.append(e.args[0])
    except Exception:
        errors.append(_('Invalid list results'))


def parse_candidate(
    line: DefaultRow,
    errors: list[str],
    election_id: str,
    colors: dict[str, str]
) -> dict[str, Any] | None:

    try:
        candidate_id = line.candidate_id
        family_name = line.candidate_family_name
        first_name = line.candidate_first_name
        elected = str(line.candidate_elected or '').lower() == 'true'
        party = line.candidate_party
        color = validate_color(line, 'candidate_party_color')
        gender = validate_gender(line)
        year_of_birth = validate_integer(
            line, 'candidate_year_of_birth', optional=True, default=None
        )

    except ValueError as e:
        errors.append(e.args[0])
    except Exception:
        errors.append(_('Invalid candidate values'))
    else:
        if party and color:
            colors[party] = color
        return {
            'id': uuid4(),
            'election_id': election_id,
            'candidate_id': candidate_id,
            'family_name': family_name,
            'first_name': first_name,
            'elected': elected,
            'party': party,
            'gender': gender,
            'year_of_birth': year_of_birth
        }
    return None


def parse_candidate_result(
    line: DefaultRow,
    errors: list[str],
    counted: bool
) -> dict[str, Any] | None:

    try:
        votes = validate_integer(line, 'candidate_votes')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return {
            'id': uuid4(),
            'votes': votes if counted else 0,
        }
    return None


def parse_candidate_panachage_headers(csv: DefaultCSVFile) -> dict[str, str]:
    headers = {}
    prefix = 'candidate_panachage_votes_from_list_'
    for header in csv.headers:
        if not header.startswith(prefix):
            continue
        parts = header.split(prefix)
        if len(parts) > 1:
            try:
                source_list_id = parts[1]
                headers[csv.as_valid_identifier(header)] = source_list_id
            except ValueError:
                pass
    return headers


def parse_candidate_panachage_results(
    line: DefaultRow,
    errors: list[str],
    values: list[dict[str, Any]],
    headers: dict[str, str]
) -> None:

    try:
        entity_id = validate_integer(line, 'entity_id')
        candidate_id = line.candidate_id
        for col_name, source in headers.items():
            votes = validate_integer(line, col_name, default=None)
            if votes:
                values.append({
                    'entity_id': entity_id,
                    'candidate_id': candidate_id,
                    'list_id': source,
                    'votes': votes
                })
    except ValueError as e:
        errors.append(e.args[0])
    except Exception:
        errors.append(_('Invalid candidate results'))


def prefix_connection_id(connection_id: str, parent_connection_id: str) -> str:
    """Used to distinguish connection ids when they have the same id
    as a parent_connection. """
    if not len(connection_id) > len(parent_connection_id):
        return parent_connection_id + connection_id
    return connection_id


def parse_connection(
    line: DefaultRow,
    errors: list[str],
    election_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:

    subconnection_id = None
    try:
        connection_id = line.list_connection
        parent_connection_id = line.list_connection_parent
        if parent_connection_id:
            subconnection_id = prefix_connection_id(
                connection_id, parent_connection_id
            )
            connection_id = parent_connection_id
    except ValueError:
        errors.append(_('Invalid list connection values'))
    else:
        connection = {
            'id': uuid4(),
            'election_id': election_id,
            'connection_id': connection_id,
        } if connection_id else None
        subconnection = {
            'id': uuid4(),
            'election_id': election_id,
            'connection_id': subconnection_id,
        } if subconnection_id else None
        return connection, subconnection
    return None, None


def import_election_internal_proporz(
    election: Election,
    principal: Canton | Municipality,
    file: IO[bytes],
    mimetype: str,
    ignore_extra: bool = False
) -> list[FileImportError]:
    """ Tries to import the given file (internal format).

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    Optionally ignores results not being part of this election.

    :return:
        A list containing errors.

    """
    filename = _('Results')
    csv, error = load_csv(
        file, mimetype, expected_headers=INTERNAL_PROPORZ_HEADERS,
        filename=filename,
        dialect='excel'
    )
    if error:
        return [error]

    assert csv is not None
    errors: list[FileImportError] = []

    candidates: dict[str, dict[str, Any]] = {}
    candidate_results = []
    lists: dict[str, dict[str, Any]] = {}
    list_results: dict[str, dict[str, Any]] = {}
    connections: dict[str, dict[str, Any]] = {}
    subconnections: dict[str, dict[str, Any]] = {}
    results: dict[int, dict[str, Any]] = {}
    list_panachage: dict[str, dict[str, Any]] = {}
    list_panachage_headers = parse_list_panachage_headers(csv)
    candidate_panachage: list[dict[str, Any]] = []
    candidate_panachage_headers = parse_candidate_panachage_headers(csv)
    entities = principal.entities[election.date.year]
    election_id = election.id
    colors = election.colors.copy()

    # This format has one candiate per entity per line
    status = None
    for line in csv.lines:
        line_errors: list[str] = []

        # Parse the line
        result = parse_election_result(
            line, line_errors, entities, election, principal, ignore_extra
        )
        if result is True:
            continue
        counted = (result or {}).get('counted', False)
        status = parse_election(line, line_errors)
        candidate = parse_candidate(line, line_errors, election_id, colors)
        candidate_result = parse_candidate_result(line, line_errors, counted)
        list_ = parse_list(line, line_errors, election_id, colors)
        list_result = parse_list_result(line, line_errors, counted)
        connection, subconnection = parse_connection(
            line, line_errors, election_id
        )
        parse_list_panachage_results(
            line, line_errors, list_panachage, list_panachage_headers
        )
        parse_candidate_panachage_results(
            line, line_errors, candidate_panachage, candidate_panachage_headers
        )

        # Skip expats if not enabled
        if result and result['entity_id'] == 0 and not election.has_expats:
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

        assert result
        assert list_ is not None
        assert list_result is not None
        assert candidate is not None
        assert candidate_result is not None

        # Add the data
        result = results.setdefault(result['entity_id'], result)

        list_ = lists.setdefault(list_['list_id'], list_)

        if connection:
            connection = connections.setdefault(
                connection['connection_id'], connection
            )
            list_['connection_id'] = connection['id']
            if subconnection:
                subconnection = subconnections.setdefault(
                    subconnection['connection_id'], subconnection
                )
                subconnection['parent_id'] = connection['id']
                list_['connection_id'] = subconnection['id']

        list_results.setdefault(result['entity_id'], {})
        list_result = list_results[result['entity_id']].setdefault(
            list_['list_id'], list_result
        )
        assert list_result is not None
        list_result['list_id'] = list_['id']

        candidate = candidates.setdefault(candidate['candidate_id'], candidate)

        candidate_result['candidate_id'] = candidate['id']
        candidate_result['election_result_id'] = result['id']
        candidate_results.append(candidate_result)

        candidate['list_id'] = list_['id']

    # Additional checks
    if not errors and not results:
        errors.append(FileImportError(_('No data found')))

    errors.extend(
        FileImportError(
            _(
                "Panachage results id ${id} not in list_id's",
                mapping={'id': list_id}
            )
        )
        for values in list_panachage.values()
        for list_id in values
        if list_id != '999' and list_id not in lists
    )

    errors.extend(
        FileImportError(
            _(
                "Panachage results id ${id} not in list_id's",
                mapping={'id': values['list_id']}
            )
        )
        for values in candidate_panachage
        if values['list_id'] != '999' and values['list_id'] not in lists
    )

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
        results[entity_id] = {
            'id': uuid4(),
            'election_id': election_id,
            'name': name,
            'district': district,
            'superregion': superregion,
            'entity_id': entity_id,
            'counted': False
        }

    # Aggregate candidate panachage to list panachage if missing
    if candidate_panachage and not any(list_panachage.values()):
        list_ids = {r['id']: r['list_id'] for r in lists.values()}
        for panachage_result in candidate_panachage:
            source = panachage_result['list_id']
            candidate_id = panachage_result['candidate_id']
            target = list_ids[candidates[candidate_id]['list_id']]
            if source == target:
                continue
            list_panachage[target].setdefault(source, 0)
            list_panachage[target][source] += panachage_result['votes'] or 0

    # Add the results to the DB
    last_result_change = election.timestamp()
    election.clear_results(True)
    election.last_result_change = last_result_change
    election.status = status
    election.colors = colors
    if election.election_compound:
        election.election_compound.last_result_change = last_result_change

    result_uids = {r['entity_id']: r['id'] for r in results.values()}
    candidate_uids = {r['candidate_id']: r['id'] for r in candidates.values()}
    list_uids = {r['list_id']: r['id'] for r in lists.values()}
    list_uids['999'] = None
    session = object_session(election)
    assert session is not None
    # FIXME: Switch to regular `session.execute` with insert statements
    session.bulk_insert_mappings(ListConnection, connections.values())  # type: ignore[arg-type]
    session.bulk_insert_mappings(ListConnection, subconnections.values())  # type: ignore[arg-type]
    session.bulk_insert_mappings(List, lists.values())  # type: ignore[arg-type]
    session.bulk_insert_mappings(ListPanachageResult, (  # type: ignore[arg-type]
        {
            'id': uuid4(),
            'source_id': list_uids[source],
            'target_id': list_uids[list_id],
            'votes': votes,
        }
        for list_id in list_panachage
        for source, votes in list_panachage[list_id].items()
    ))
    session.bulk_insert_mappings(Candidate, candidates.values())  # type: ignore[arg-type]
    session.bulk_insert_mappings(ElectionResult, results.values())  # type: ignore[arg-type]
    session.bulk_insert_mappings(ListResult, (  # type: ignore[arg-type]
        dict(**list_result, election_result_id=result_uids[entity_id])
        for entity_id, values in list_results.items()
        for list_result in values.values()
    ))
    session.bulk_insert_mappings(CandidateResult, candidate_results)  # type: ignore[arg-type]
    session.bulk_insert_mappings(CandidatePanachageResult, (  # type: ignore[arg-type]
        {
            'id': uuid4(),
            'election_result_id': result_uids[panachage_result['entity_id']],
            'source_id': list_uids[panachage_result['list_id']],
            'target_id': candidate_uids[panachage_result['candidate_id']],
            'votes': panachage_result['votes'],
        }
        for panachage_result in candidate_panachage
    ))
    session.flush()
    session.expire_all()

    return []
