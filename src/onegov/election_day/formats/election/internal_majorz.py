from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import get_entity_and_district
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import STATI
from onegov.election_day.formats.common import validate_gender
from onegov.election_day.formats.common import validate_integer
from onegov.election_day.formats.mappings import INTERNAL_MAJORZ_HEADERS
from sqlalchemy.orm import object_session
from uuid import uuid4


def parse_election(line, errors):
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
    return majority, status


def parse_election_result(line, errors, entities, election, principal):
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

        else:
            name, district, superregion = get_entity_and_district(
                entity_id, entities, election, principal, errors
            )

            if not errors:
                return dict(
                    id=uuid4(),
                    election_id=election.id,
                    name=name,
                    district=district,
                    superregion=superregion,
                    entity_id=entity_id,
                    counted=counted,
                    eligible_voters=eligible_voters,
                    expats=expats,
                    received_ballots=received_ballots,
                    blank_ballots=blank_ballots,
                    invalid_ballots=invalid_ballots,
                    blank_votes=blank_votes,
                    invalid_votes=invalid_votes,
                )


def parse_candidate(line, errors, election_id):
    try:
        id = validate_integer(line, 'candidate_id')
        family_name = line.candidate_family_name
        first_name = line.candidate_first_name
        elected = str(line.candidate_elected or '').lower() == 'true'
        party = line.candidate_party
        gender = validate_gender(line)
        year_of_birth = validate_integer(
            line, 'candidate_year_of_birth', optional=True, default=None
        )

    except ValueError as e:
        errors.append(e.args[0])
    except Exception:
        errors.append(_("Invalid candidate values"))
    else:
        return dict(
            id=uuid4(),
            candidate_id=id,
            election_id=election_id,
            family_name=family_name,
            first_name=first_name,
            elected=elected,
            party=party,
            gender=gender,
            year_of_birth=year_of_birth
        )


def parse_candidate_result(line, errors):
    try:
        votes = validate_integer(line, 'candidate_votes')
    except ValueError as e:
        errors.append(e.args[0])
    else:
        return dict(
            id=uuid4(),
            votes=votes,
        )


def import_election_internal_majorz(election, principal, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.Election.export().

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
    if error:
        return [error]

    errors = []
    candidates = {}
    candidate_results = []
    results = {}
    entities = principal.entities[election.date.year]
    election_id = election.id

    # This format has one candiate per entity per line
    absolute_majority = None
    status = None
    for line in csv.lines:
        line_errors = []

        # Parse the line
        absolute_majority, status = parse_election(line, line_errors)
        result = parse_election_result(
            line, line_errors, entities, election, principal
        )
        candidate = parse_candidate(line, line_errors, election_id)
        candidate_result = parse_candidate_result(line, line_errors)

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

        # Add the data
        result = results.setdefault(result['entity_id'], result)

        candidate = candidates.setdefault(candidate['candidate_id'], candidate)
        candidate_result['candidate_id'] = candidate['id']
        candidate_result['election_result_id'] = result['id']
        candidate_results.append(candidate_result)

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
        results[entity_id] = dict(
            id=uuid4(),
            election_id=election_id,
            name=name,
            district=district,
            superregion=superregion,
            entity_id=entity_id,
            counted=False
        )

    # Add the results to the DB
    election.clear_results()
    election.last_result_change = election.timestamp()
    election.absolute_majority = absolute_majority
    election.status = status

    session = object_session(election)
    session.bulk_insert_mappings(Candidate, candidates.values())
    session.bulk_insert_mappings(ElectionResult, results.values())
    session.bulk_insert_mappings(CandidateResult, candidate_results)

    return []
