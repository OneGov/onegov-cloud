from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.utils import clear_election
from uuid import uuid4


HEADERS = [
    'anzmandate',
    'bfs',
    'einheitbez',
    'stimmber',
    'stimmabgegeben',
    'stimmleer',
    'stimmungueltig',
]

HEADERS_RESULT = [
    'id',
    'name',
    'vorname',
]


def parse_election(line, errors):
    try:
        mandates = int(line.anzmandate or 0)
    except ValueError:
        errors.append(_("Invalid election values"))
    else:
        return mandates


def parse_election_result(line, errors, entities):
    try:
        group = line.einheitbez.strip()
        entity_id = int(line.bfs or 0)
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


def parse_candidates(line, errors):
    results = []
    index = 0
    while True:
        index += 1
        try:
            id = getattr(line, 'kandid_{}'.format(index))
            family_name = getattr(line, 'kandname_{}'.format(index))
            first_name = getattr(line, 'kandvorname_{}'.format(index))
            votes = int(getattr(line, 'stimmen_{}'.format(index)) or 0)
        except AttributeError:
            break
        except ValueError:
            errors.append(_("Invalid candidate values"))
            break
        else:
            skip = ('Vereinzelte', 'Leere Zeilen', 'Ungültige Stimmen')
            if family_name in skip:
                continue
            results.append((
                Candidate(
                    id=uuid4(),
                    candidate_id=id,
                    family_name=family_name,
                    first_name=first_name,
                    elected=False
                ),
                CandidateResult(
                    id=uuid4(),
                    votes=votes,
                )
            ))
    return results


def import_election_wabsti_majorz(
    election, entities, file, mimetype,
    elected_file=None, elected_mimetype=None
):
    errors = []
    candidates = {}
    results = []

    # This format has one entity per line and every candidate as row
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename
    )
    if error:
        errors.append(error)
    else:
        mandates = 0
        for line in csv.lines:
            line_errors = []

            # Parse the line
            mandates = parse_election(line, line_errors)
            result = parse_election_result(line, line_errors, entities)
            if result:
                for candidate, c_result in parse_candidates(line, line_errors):
                    candidate = candidates.setdefault(
                        candidate.candidate_id, candidate
                    )
                    c_result.candidate_id = candidate.id
                    result.candidate_results.append(c_result)

            # Pass the errors and continue to next line
            if line_errors:
                errors.extend(
                    FileImportError(
                        error=err, line=line.rownumber, filename=filename
                    )
                    for err in line_errors
                )
                continue

            results.append(result)

    # The results file has one elected candidate per line
    filename = _("Elected Candidates")
    if elected_file and elected_mimetype:
        csv, error = load_csv(
            elected_file, elected_mimetype, expected_headers=HEADERS_RESULT,
            filename=filename
        )
        if error:
            errors.append(error)
        else:
            for line in csv.lines:
                line_errors = []

                if line.id in candidates and \
                        candidates[line.id].family_name == line.name and \
                        candidates[line.id].first_name == line.vorname:
                    candidates[line.id].elected = True
                else:
                    errors.append(
                        FileImportError(
                            error=_("Unknown candidate"),
                            line=line.rownumber,
                            filename=filename
                        )
                    )

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return errors

    if results:
        clear_election(election)

        election.number_of_mandates = mandates
        election.counted_entities = len(results)
        election.total_entities = max(len(entities), len(results))

        for candidate in candidates.values():
            election.candidates.append(candidate)

        for result in results:
            election.results.append(result)

    return []
