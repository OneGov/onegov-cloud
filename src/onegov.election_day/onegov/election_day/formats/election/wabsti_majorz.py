from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from uuid import uuid4


HEADERS = [
    'anzmandate',
    # 'absolutesmehr' optional
    'bfs',
    'stimmber',
    # 'stimmabgegeben' or 'wzabgegeben'
    # 'wzleer' or 'stimmleer'
    # 'wzungueltig' or 'stimmungueltig'
]

HEADERS_CANDIDATES = [
    'kandid',
]


def parse_election(line, errors):
    mandates = None
    majority = None
    try:
        mandates = int(line.anzmandate or 0)
        if hasattr(line, 'absolutesmehr'):
            majority = int(line.absolutesmehr or 0)
            majority = majority if majority > 0 else None
    except ValueError:
        errors.append(_("Invalid election values"))

    return mandates, majority


def parse_election_result(line, errors, entities, added_entities):
    try:
        entity_id = int(line.bfs or 0)
        eligible_voters = int(line.stimmber or 0)
        received_ballots = int(
            getattr(line, 'wzabgegeben', 0) or
            getattr(line, 'stimmabgegeben', 0)
        )
        blank_ballots = int(
            getattr(line, 'wzleer', 0) or
            getattr(line, 'stimmleer', 0)
        )
        invalid_ballots = int(
            getattr(line, 'wzungueltig', 0) or
            getattr(line, 'stimmungueltig', 0)
        )

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

    except ValueError:
        errors.append(_("Invalid entity values"))
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
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
                counted=True,
                entity_id=entity_id,
                eligible_voters=eligible_voters,
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
            candidate_id = getattr(line, 'kandid_{}'.format(index), str(index))
            family_name = getattr(line, 'kandname_{}'.format(index))
            first_name = getattr(line, 'kandvorname_{}'.format(index))
            votes = int(getattr(line, 'stimmen_{}'.format(index)) or 0)
            elected = False
            if hasattr(line, 'kandresultart_{}'.format(index)):
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
                    candidate_id=candidate_id,
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


def import_election_wabsti_majorz(
    election, principal, file, mimetype,
    elected_file=None, elected_mimetype=None
):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for majorz elections. Since there is no
    format description, importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """

    errors = []
    candidates = {}
    results = {}
    added_entities = set()
    entities = principal.entities[election.date.year]

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
        majority = None
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

            results.setdefault(result.entity_id, result)

    # The candidates file has one elected candidate per line
    filename = _("Elected Candidates")
    if elected_file and elected_mimetype:
        csv, error = load_csv(
            elected_file, elected_mimetype,
            expected_headers=HEADERS_CANDIDATES,
            filename=filename
        )
        if error:
            # Wabsti files are sometimes UTF-16
            csv, utf16_error = load_csv(
                elected_file, elected_mimetype,
                expected_headers=HEADERS_CANDIDATES, encoding='utf-16-le'
            )
            if utf16_error:
                errors.append(error)
            else:
                error = None
        if not error:
            for line in csv.lines:
                try:
                    candidate_id = line.kandid
                except ValueError:
                    errors.append(
                        FileImportError(
                            error=_("Invalid values"),
                            line=line.rownumber,
                            filename=filename
                        )
                    )
                else:
                    if candidate_id in candidates:
                        candidates[candidate_id].elected = True
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

    # Check if all results are from the same district if regional election
    districts = set([result.district for result in results.values()])
    if election.domain == 'region' and election.distinct:
        if principal.has_districts:
            if len(districts) != 1:
                errors.append(FileImportError(_("No clear district")))
        else:
            if len(results) != 1:
                errors.append(FileImportError(_("No clear district")))

    if errors:
        return errors

    # Add the missing entities
    remaining = entities.keys() - results.keys()
    for entity_id in remaining:
        entity = entities[entity_id]
        district = entity.get('district', '')
        if election.domain == 'region':
            if not election.distinct:
                continue
            if not principal.has_districts:
                continue
            if district not in districts:
                continue
        results[entity_id] = ElectionResult(
            id=uuid4(),
            name=entity.get('name', ''),
            district=district,
            entity_id=entity_id,
            counted=False
        )

    election.clear_results()
    election.number_of_mandates = mandates
    election.absolute_majority = majority

    for candidate in candidates.values():
        election.candidates.append(candidate)

    for result in results.values():
        election.results.append(result)

    return []
