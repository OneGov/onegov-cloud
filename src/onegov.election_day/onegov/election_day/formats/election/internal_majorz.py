from csv import excel
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
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
    'entity_elegible_voters',
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
            entity = entities.get(entity_id, {})
            return ElectionResult(
                id=uuid4(),
                name=entity.get('name', ''),
                district=entity.get('district', ''),
                entity_id=entity_id,
                elegible_voters=elegible_voters,
                received_ballots=received_ballots,
                blank_ballots=blank_ballots,
                invalid_ballots=invalid_ballots,
                blank_votes=blank_votes,
                invalid_votes=invalid_votes,
            )


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


def import_election_internal_majorz(election, entities, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.Election.export().

    :return:
        A list containing errors.

    """
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename,
        dialect=excel
    )
    if error:
        return [error]

    errors = []

    candidates = {}
    results = {}

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

        candidate = candidates.setdefault(candidate.candidate_id, candidate)
        candidate_result.candidate_id = candidate.id
        result.candidate_results.append(candidate_result)

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return errors

    # todo: Add missing entities as uncounted

    if results:
        election.clear_results()

        election.absolute_majority = absolute_majority
        election.status = status
        election.counted_entities = counted
        election.total_entities = total

        for candidate in candidates.values():
            election.candidates.append(candidate)

        for result in results.values():
            election.results.append(result)

    return []
