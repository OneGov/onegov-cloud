from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.formats.imports.common import validate_color
from onegov.election_day.formats.imports.common import validate_integer
from onegov.election_day.formats.imports.common import validate_list_id
from onegov.election_day.formats.imports.common import validate_numeric
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import PartyPanachageResult
from onegov.election_day.models import PartyResult
from uuid import uuid4


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.csv import DefaultCSVFile
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.models import ProporzElection


ELECTION_PARTY_HEADERS = (
    'year',
    'name',
    'id',
    'color',
    # 'mandates', optional
    # 'votes', optional
    # 'total_votes', optional
    # 'voters_count'  optional
    # 'voters_count_percentage' optional
)


def parse_domain(
    line: DefaultRow,
    errors: list[str],
    election: ProporzElection | ElectionCompound,
    principal: Canton | Municipality,
    election_year: int
) -> tuple[bool, str | None, str | None]:
    """ Parse domain and domain segment. Also indicate, if line should be
    skipped.

    """

    domain = getattr(line, 'domain', None) or None
    domain_segment = (
        getattr(line, 'domain_segment', None)
        or getattr(line, 'domain_id', None)
        or None
    )

    if isinstance(election, ElectionCompound):
        # Compound (including results for superregions)
        if not domain or domain == election.domain:
            return False, election.domain, None
        if domain == 'superregion':
            if domain_segment not in principal.get_superregions(election_year):
                errors.append(
                    _(
                        'Invalid domain_segment: ${domain_segment}',
                        mapping={'domain_segment': domain_segment}
                    )
                )
                return False, None, None
            return False, domain, domain_segment
    else:
        # Election
        if not domain or domain == election.domain:
            if (
                not domain_segment
                or domain_segment == election.domain_segment
            ):
                return False, election.domain, election.domain_segment

    return True, None, None


def parse_party_result(
    line: DefaultRow,
    errors: list[str],
    party_results: dict[str, PartyResult],
    totals: dict[int, dict[tuple[str | None, str | None], int | None]],
    parties: set[str],
    election_year: int,
    locales: Collection[str],
    default_locale: str,
    colors: dict[str, str],
    domain: str | None,
    domain_segment: str | None
) -> None:

    totals_key = (domain, domain_segment)
    try:
        year = validate_integer(line, 'year', default=election_year)

        name_translations = {
            locale: getattr(line, f'name_{locale.lower()}', '').strip()
            for locale in locales
        }
        name_translations = {
            locale: name for locale, name in name_translations.items()
            if name
        }
        if hasattr(line, 'name'):
            if not name_translations.get(default_locale):
                name_translations[default_locale] = line.name or ''

        party_id = validate_list_id(line, 'id')
        color = validate_color(line, 'color')
        mandates = validate_integer(
            line, 'mandates', optional=True, default=None
        )
        votes = validate_integer(
            line, 'votes', optional=True, default=None
        )
        total_votes = validate_integer(
            line, 'total_votes', optional=True, default=None
        )
        voters_count = validate_numeric(
            line, 'voters_count', precision=12, scale=2,
            optional=True, default=None
        )
        voters_count_percentage = validate_numeric(
            line, 'voters_count_percentage', precision=12, scale=2,
            optional=True, default=None
        )
        assert all((year, name_translations.get(default_locale)))

        totals.setdefault(year, {})
        assert totals[year].get(totals_key, total_votes) == total_votes
    except ValueError as e:
        errors.append(e.args[0])
    except AssertionError:
        errors.append(_('Invalid values'))
    else:
        key = f'{domain}/{domain_segment}/{year}/{party_id}'
        totals[year][totals_key] = total_votes
        if year == election_year:
            parties.add(party_id)

        if key in party_results:
            errors.append(_('${name} was found twice', mapping={'name': key}))
        else:
            party_results[key] = PartyResult(
                id=uuid4(),
                domain=domain,
                domain_segment=domain_segment,
                party_id=party_id,
                year=year,
                total_votes=total_votes or 0,
                name_translations=name_translations,
                number_of_mandates=mandates or 0,
                votes=votes or 0,
                voters_count=voters_count,
                voters_count_percentage=voters_count_percentage
            )
            if color:
                for name in name_translations.values():
                    colors[name] = color


def parse_panachage_headers(csv: DefaultCSVFile) -> dict[str, str]:
    headers = {}
    for header in csv.headers:
        if not header.startswith('panachage_votes_from_'):
            continue
        parts = header.split('panachage_votes_from_')
        if len(parts) > 1:
            headers[csv.as_valid_identifier(header)] = parts[1]
    return headers


def parse_panachage_results(
    line: DefaultRow,
    errors: list[str],
    results: dict[str, dict[str, int]],
    headers: dict[str, str],
    election_year: int
) -> None:

    try:
        target = validate_list_id(line, 'id')
        year = validate_integer(line, 'year', default=election_year)
        if target not in results and year == election_year:
            results[target] = {}
            for col_name, source in headers.items():
                if source == target:
                    continue
                results[target][source] = validate_integer(line, col_name)

    except ValueError as e:
        errors.append(e.args[0])


def import_party_results_internal(
    election: ProporzElection | ElectionCompound,
    principal: Canton | Municipality,
    file: IO[bytes],
    mimetype: str,
    locales: Collection[str],
    default_locale: str
) -> list[FileImportError]:
    """ Tries to import the given file.

    This is our own format used for party results. Supports per party panachage
    data. Stores the panachage results from the blank list with a blank name.

    :return:
        A list containing errors.

    """

    errors = []
    parties: set[str] = set()
    party_results: dict[str, PartyResult] = {}
    party_totals: dict[int, dict[tuple[str | None, str | None], int | None]]
    party_totals = {}
    panachage_results: dict[str, dict[str, int]] = {}
    panachage_headers = None
    colors = election.colors.copy()

    # The party results file has one party per year per line (but only
    # panachage results in the year of the election)
    if file and mimetype:
        csv, error = load_csv(
            file, mimetype, expected_headers=ELECTION_PARTY_HEADERS)
        if error:
            errors.append(error)
        else:
            assert csv is not None
            panachage_headers = parse_panachage_headers(csv)
            for line in csv.lines:
                line_errors: list[str] = []
                skip, domain, domain_segment = parse_domain(
                    line, line_errors,
                    election, principal, election.date.year
                )
                if skip:
                    continue

                parse_party_result(
                    line, line_errors,
                    party_results, party_totals, parties,
                    election.date.year,
                    locales, default_locale,
                    colors,
                    domain, domain_segment
                )
                if domain == election.domain:
                    parse_panachage_results(
                        line, line_errors,
                        panachage_results, panachage_headers,
                        election.date.year
                    )
                if line_errors:
                    errors.extend(
                        FileImportError(error=err, line=line.rownumber)
                        for err in line_errors
                    )

    if not parties:
        errors.append(FileImportError(
            _(
                'No party results for year ${year}',
                mapping={'year': election.date.year}
            )
        ))

    if panachage_headers and parties:
        for list_id in panachage_headers.values():
            if list_id != '999' and list_id not in parties:
                errors.append(FileImportError(
                    _('Panachage results ids and id not consistent'))
                )
                break

    if errors:
        return errors

    election.party_results = []
    election.party_panachage_results = []

    election.colors = colors
    election.last_result_change = election.timestamp()

    for result in party_results.values():
        election.party_results.append(result)

    for target in panachage_results:
        if target in parties:
            for source, votes in panachage_results[target].items():
                if source in parties or source == '999':
                    election.party_panachage_results.append(
                        PartyPanachageResult(
                            id=uuid4(),
                            source=source if source != '999' else '',
                            target=target,
                            votes=votes
                        )
                    )

    return []
