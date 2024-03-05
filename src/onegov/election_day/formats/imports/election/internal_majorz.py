from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import STATI
from onegov.election_day.formats.imports.common import validate_color
from onegov.election_day.formats.imports.common import validate_gender
from onegov.election_day.formats.imports.common import validate_integer


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Election
    from onegov.ballot.types import Status
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


INTERNAL_MAJORZ_HEADERS = (
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
    'election_absolute_majority',
)


def parse_election(
    line: 'DefaultRow',
    errors: list[str]
) -> tuple[int | None, 'Status | None']:

    majority = None
    status = None
    try:
        if line.election_absolute_majority:
            majority = validate_integer(line, 'election_absolute_majority')
            majority = majority if majority else None
        status = line.election_status or 'unknown'

    except ValueError as e:
        errors.append(e.args[0])

    except Exception:
        errors.append(_("Invalid election values"))
    if status not in STATI:
        errors.append(_("Invalid status"))
    return majority, status  # type:ignore[return-value]


def parse_election_result(
    line: 'DefaultRow',
    errors: list[str],
    entities: dict[int, dict[str, str]],
    election: 'Election',
    principal: 'Canton | Municipality',
    processed_results: dict[int, ElectionResult],
    existing_results: dict[int, ElectionResult]
) -> ElectionResult | None:

    # Get entity_id
    try:
        entity_id = validate_integer(line, 'entity_id')
    except ValueError as e:
        errors.append(e.args[0])
        return None
    except Exception:
        errors.append(_("Invalid entity values"))
        return None

    # Check if already processed
    result = processed_results.get(entity_id)
    if result:
        return result

    # Parse
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
    except Exception:
        errors.append(_("Invalid entity values"))
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0
        if entity_id and entity_id not in entities:
            errors.append(_(
                "${name} is unknown",
                mapping={'name': entity_id}
            ))
            return None

        # Skip expats if not enabled
        if entity_id == 0 and not election.has_expats:
            return None

        # Get existing or create new one
        result = existing_results.get(entity_id)
        if not result:
            result = ElectionResult(entity_id=entity_id)
        processed_results[entity_id] = result

        # Update
        name, district, superregion = get_entity_and_district(
            entity_id, entities, election, principal, errors
        )
        result.name = name
        result.district = district
        result.superregion = superregion
        result.entity_id = entity_id
        result.counted = counted
        result.eligible_voters = eligible_voters if counted else 0
        result.expats = expats if counted else 0
        result.received_ballots = received_ballots if counted else 0
        result.blank_ballots = blank_ballots if counted else 0
        result.invalid_ballots = invalid_ballots if counted else 0
        result.blank_votes = blank_votes if counted else 0
        result.invalid_votes = invalid_votes if counted else 0
        return result

    return None


def parse_candidate(
    line: 'DefaultRow',
    errors: list[str],
    colors: dict[str, str],
    processed_candidates: dict[str, Candidate],
    existing_candidates: dict[str, Candidate]
) -> Candidate | None:

    # Get candidate id
    if not hasattr(line, 'candidate_id'):
        errors.append(_("Invalid candidate values"))
        return None
    candidate_id = line.candidate_id

    # Check if already processed
    candidate = processed_candidates.get(candidate_id)
    if candidate:
        return candidate

    # Parse
    try:
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
        errors.append(_("Invalid candidate values"))
    else:
        # Get existing or create a new
        candidate = existing_candidates.get(candidate_id)
        if not candidate:
            candidate = Candidate(candidate_id=candidate_id)
        processed_candidates[candidate_id] = candidate

        # Update
        if party and color:
            colors[party] = color
        candidate.candidate_id = candidate_id
        candidate.family_name = family_name
        candidate.first_name = first_name
        candidate.elected = elected
        candidate.party = party
        candidate.gender = gender
        candidate.year_of_birth = year_of_birth
        return candidate

    return None


def parse_candidate_votes(
    line: 'DefaultRow',
    errors: list[str],
) -> int | None:

    try:
        votes = validate_integer(line, 'candidate_votes')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return votes
    return None


def import_election_internal_majorz(
    election: 'Election',
    principal: 'Canton | Municipality',
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
    """ Tries to import the given file (internal format).

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=INTERNAL_MAJORZ_HEADERS,
        filename=filename,
        dialect='excel'
    )
    if error is not None:
        return [error]

    assert csv is not None
    errors: list[FileImportError] = []
    candidates: dict[str, Candidate] = {}
    existing_candidates = {
        candidate.candidate_id: candidate for candidate in election.candidates
    }
    existing_candidate_results = {
        (candidate.candidate_id, result.election_result.entity_id):
        result for candidate in election.candidates
        for result in candidate.results
    }
    results: dict[int, ElectionResult] = {}
    existing_results = {
        result.entity_id: result for result in election.results
    }
    entities = principal.entities[election.date.year]
    colors = election.colors.copy()

    # This format has one candiate per entity per line
    absolute_majority = None
    status = None
    for line in csv.lines:
        line_errors: list[str] = []

        # Parse the line
        absolute_majority, status = parse_election(line, line_errors)
        result = parse_election_result(
            line, line_errors, entities, election, principal, results,
            existing_results
        )
        candidate = parse_candidate(
            line, line_errors, colors, candidates, existing_candidates
        )
        votes = parse_candidate_votes(line, line_errors) or 0

        # Pass the errors and continue to the next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename=filename
                )
                for err in line_errors
            )
            continue

        # Add the candidate results
        if result and candidate:
            candidate_result = existing_candidate_results.get(
                (candidate.candidate_id, result.entity_id)
            )
            if not candidate_result:
                candidate_result = CandidateResult()
                result.candidate_results.append(candidate_result)
                candidate.results.append(candidate_result)
            candidate_result.votes = votes if result.counted else 0

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

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
            name=name,
            district=district,
            superregion=superregion,
            entity_id=entity_id,
            counted=False,
            eligible_voters=0,
            expats=0,
            received_ballots=0,
            blank_ballots=0,
            invalid_ballots=0,
            blank_votes=0,
            invalid_votes=0
        )

    # Add the results
    election.last_result_change = election.timestamp()
    election.absolute_majority = absolute_majority
    election.status = status
    election.colors = colors
    election.candidates = list(candidates.values())
    election.results = list(results.values())

    return []
