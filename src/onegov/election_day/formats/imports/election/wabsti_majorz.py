from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_integer
from uuid import uuid4


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Election
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


WABSTI_MAJORZ_HEADERS = (
    'anzmandate',
    # 'absolutesmehr' optional
    'bfs',
    'stimmber',
    # 'stimmabgegeben' or 'wzabgegeben'
    # 'wzleer' or 'stimmleer'
    # 'wzungueltig' or 'stimmungueltig'
)

WABSTI_MAJORZ_HEADERS_CANDIDATES = (
    'kandid',
)


def parse_election(
    line: 'DefaultRow',
    errors: list[str]
) -> tuple[int | None, int | None]:

    mandates = None
    majority = None
    try:
        mandates = validate_integer(line, 'anzmandate')
        if hasattr(line, 'absolutesmehr'):
            majority = validate_integer(line, 'absolutesmehr')
            majority = majority if majority > 0 else None

    except ValueError as e:
        errors.append(e.args[0])

    except Exception:
        errors.append(_("Invalid election values"))

    return mandates, majority


def parse_election_result(
    line: 'DefaultRow',
    errors: list[str],
    entities: dict[int, dict[str, str]],
    added_entities: set[int],
    election: 'Election',
    principal: 'Canton | Municipality'
) -> ElectionResult | None:

    try:
        entity_id = validate_integer(line, 'bfs')
        eligible_voters = validate_integer(line, 'stimmber')
        received_ballots = int(
            getattr(line, 'wzabgegeben', 0)
            or getattr(line, 'stimmabgegeben', 0)
        )
        blank_ballots = int(
            getattr(line, 'wzleer', 0)
            or getattr(line, 'stimmleer', 0)
        )
        invalid_ballots = int(
            getattr(line, 'wzungueltig', 0)
            or getattr(line, 'stimmungueltig', 0)
        )

        blank_votes = None
        invalid_votes = None
        count = 0
        while True:
            count += 1
            try:
                name = getattr(line, f'kandname_{count}')
                votes = validate_integer(line, f'stimmen_{count}')
            except AttributeError:
                break
            except Exception:
                raise
            else:
                if name == 'Leere Zeilen':
                    blank_votes = votes
                elif name == 'Ungültige Stimmen':
                    invalid_votes = votes

        # FIXME: I think SQLAlchemy's default __init__ just uses
        #        a column's default value if it's not nullable
        #        and the value passed in was `None`, so if we
        #        actually want to report an error if this data is
        #        missing then we need to assert here.
        # assert blank_votes is not None
        # assert invalid_votes is not None

    except ValueError as e:
        errors.append(e.args[0])
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
            name, district, superregion = get_entity_and_district(
                entity_id, entities, election, principal, errors
            )

            if not errors:
                added_entities.add(entity_id)
                return ElectionResult(  # type:ignore[misc]
                    id=uuid4(),
                    name=name,
                    district=district,
                    superregion=superregion,
                    counted=True,
                    entity_id=entity_id,
                    eligible_voters=eligible_voters,
                    received_ballots=received_ballots,
                    blank_ballots=blank_ballots,
                    invalid_ballots=invalid_ballots,
                    blank_votes=blank_votes,
                    invalid_votes=invalid_votes,
                )
    return None


def parse_candidates(
    line: 'DefaultRow',
    errors: list[str]
) -> list[tuple[Candidate, CandidateResult]]:

    results = []
    index = 0
    while True:
        index += 1
        try:
            candidate_id = getattr(line, f'kandid_{index}', str(index))
            family_name = getattr(line, f'kandname_{index}')
            first_name = getattr(line, f'kandvorname_{index}')
            votes = validate_integer(line, f'stimmen_{index}')
            elected = False
            if hasattr(line, f'kandresultart_{index}'):
                elected = validate_integer(line, f'kandresultart_{index}') == 2
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
    election: 'Election',
    principal: 'Canton | Municipality',
    file: IO[bytes],
    mimetype: str,
    elected_file: IO[bytes] | None = None,
    elected_mimetype: str | None = None
) -> list[FileImportError]:
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for majorz elections. Since there is no
    format description, importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """

    errors = []
    candidates: dict[str, Candidate] = {}
    results: dict[int, ElectionResult] = {}
    added_entities: set[int] = set()
    entities = principal.entities[election.date.year]

    # This format has one entity per line and every candidate as row
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=WABSTI_MAJORZ_HEADERS,
        filename=filename
    )
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype,
            expected_headers=WABSTI_MAJORZ_HEADERS,
            encoding='utf-16-le'
        )
        if utf16_error:
            errors.append(error)
        else:
            error = None

    if not error:
        assert csv is not None
        mandates: int | None = 0
        majority = None
        for line in csv.lines:
            line_errors: list[str] = []

            # Parse the line
            mandates, majority = parse_election(line, line_errors)
            result = parse_election_result(
                line, line_errors, entities, added_entities, election,
                principal
            )
            if result:
                for candidate, c_result in parse_candidates(line, line_errors):
                    candidate = candidates.setdefault(
                        candidate.candidate_id, candidate
                    )
                    c_result.candidate_id = candidate.id
                    result.candidate_results.append(c_result)

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

            assert result is not None
            results.setdefault(result.entity_id, result)

    # The candidates file has one elected candidate per line
    filename = _("Elected Candidates")
    if elected_file and elected_mimetype:
        csv, error = load_csv(
            elected_file, elected_mimetype,
            expected_headers=WABSTI_MAJORZ_HEADERS_CANDIDATES,
            filename=filename
        )
        if error:
            # Wabsti files are sometimes UTF-16
            csv, utf16_error = load_csv(
                elected_file, elected_mimetype,
                expected_headers=WABSTI_MAJORZ_HEADERS_CANDIDATES,
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
    election.number_of_mandates = mandates or 0
    election.absolute_majority = majority

    for candidate in candidates.values():
        election.candidates.append(candidate)

    for result in results.values():
        election.results.append(result)

    return []
