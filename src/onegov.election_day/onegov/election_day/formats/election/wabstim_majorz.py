from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from uuid import uuid4


HEADERS = [
    'anzmandate',
    'absolutesmehr',
    'bfs',
    'stimmber',
    'wzabgegeben',
    'wzleer',
    'wzungueltig',
]


def parse_election(line, errors):
    mandates = None
    majority = None
    try:
        mandates = int(line.anzmandate or 0)
        majority = int(line.absolutesmehr or 0)
    except ValueError:
        errors.append(_("Invalid election values"))

    return mandates, majority


def parse_election_result(line, errors, entities, added_entities):
    try:
        entity_id = int(line.bfs or 0)
        elegible_voters = int(line.stimmber or 0)
        received_ballots = int(line.wzabgegeben or 0)
        blank_ballots = int(line.wzleer or 0)
        invalid_ballots = int(line.wzungueltig or 0)

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
            except Exception:
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
        if entity_id not in entities:
            errors.append(_(
                _("${name} is unknown", mapping={'name': entity_id})
            ))
        elif entity_id in added_entities:
            errors.append(
                _("${name} was found twice", mapping={
                    'name': entity_id
                }))
        else:
            added_entities.add(entity_id)
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


def parse_candidates(line, errors):
    results = []
    index = 0
    while True:
        index += 1
        try:
            family_name = getattr(line, 'kandname_{}'.format(index))
            first_name = getattr(line, 'kandvorname_{}'.format(index))
            votes = int(getattr(line, 'stimmen_{}'.format(index)) or 0)
            elected = int(
                getattr(line, 'kandresultart_{}'.format(index)) or 0
            ) == 2
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
                    candidate_id=str(index),
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


def import_election_wabstim_majorz(
    election, entities, file, mimetype
):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for majorz elections for municipalities.
    Since there is no format description, importing these files is somewhat
    experimental.

    :return:
        A list containing errors.

    """

    errors = []
    candidates = {}
    results = []
    added_entities = set()

    # This format has one entity per line and every candidate as row
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename
    )
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype, expected_headers=HEADERS, encoding='utf-16-le'
        )
        if utf16_error:
            errors.append(error)
        else:
            error = None
    if not error:
        mandates = 0
        majority = 0
        for line in csv.lines:
            line_errors = []

            # Parse the line
            mandates, majority = parse_election(line, line_errors)
            result = parse_election_result(
                line, line_errors, entities, added_entities
            )
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

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return errors

    # todo: Add missing entities as uncounted

    if results:
        election.clear_results()

        election.number_of_mandates = mandates
        election.absolute_majority = majority
        election.counted_entities = len(results)
        election.total_entities = max(len(entities), len(results))

        for candidate in candidates.values():
            election.candidates.append(candidate)

        for result in results:
            election.results.append(result)

    return []
