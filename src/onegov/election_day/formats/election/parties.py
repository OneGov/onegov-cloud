from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError, \
    validate_integer, validate_list_id
from onegov.election_day.formats.common import load_csv
from re import match
from sqlalchemy.orm import object_session
from uuid import uuid4

from onegov.election_day.import_export.mappings import \
    ELECTION_PARTY_HEADERS


def parse_party_result(
        line, errors, party_results, totals, parties, election_year):
    try:
        year = validate_integer(line, 'year', default=election_year)
        total_votes = validate_integer(line, 'total_votes')
        name = line.name or ''
        id_ = validate_list_id(line, 'id')
        color = line.color or (
            '#0571b0' if year == election_year else '#999999'
        )
        mandates = validate_integer(line, 'mandates')
        votes = validate_integer(line, 'votes')
        assert all((year, total_votes, name, color))
        assert match(r'^#[0-9A-Fa-f]{6}$', color)
        assert totals.get(year, total_votes) == total_votes
    except ValueError as e:
        errors.append(e.args[0])
    except AssertionError:
        errors.append(_("Invalid values"))
    else:
        key = '{}/{}'.format(name, year)
        totals[year] = total_votes
        if year == election_year:
            parties[id_] = name

        if key in party_results:
            errors.append(_("${name} was found twice", mapping={'name': key}))
        else:
            party_results[key] = PartyResult(
                id=uuid4(),
                year=year,
                total_votes=total_votes,
                name=name,
                color=color,
                number_of_mandates=mandates,
                votes=votes
            )


def parse_panachage_headers(csv):
    headers = {}
    for header in csv.headers:
        if not header.startswith('panachage_votes_from_'):
            continue
        parts = header.split('panachage_votes_from_')
        if len(parts) > 1:
            headers[csv.as_valid_identifier(header)] = parts[1]
    return headers


def parse_panachage_results(line, errors, results, headers, election_year):
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


def import_party_results(election, file, mimetype):
    """ Tries to import the given file.

    This is our own format used for party results. Supports per party panachage
    data. Stores the panachage results from the blank list with a blank name.

    :return:
        A list containing errors.

    """

    errors = []
    parties = {}
    party_results = {}
    party_totals = {}
    panachage_results = {}
    panachage_headers = None

    # The party results file has one party per year per line (but only
    # panachage results in the year of the election)
    if file and mimetype:
        csv, error = load_csv(
            file, mimetype, expected_headers=ELECTION_PARTY_HEADERS)
        if error:
            errors.append(error)
        else:
            panachage_headers = parse_panachage_headers(csv)
            for line in csv.lines:
                line_errors = []
                parse_party_result(
                    line, line_errors,
                    party_results, party_totals, parties,
                    election.date.year
                )
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

    if panachage_headers:
        for list_id in panachage_headers.values():
            if not list_id == '999' and list_id not in parties.keys():
                errors.append(FileImportError(
                    _("Panachage results ids and id not consistent")))
                break

    if errors:
        return errors

    session = object_session(election)
    for result in election.party_results:
        session.delete(result)
    for result in election.panachage_results:
        session.delete(result)

    for result in party_results.values():
        election.party_results.append(result)

    for target in panachage_results:
        if target in parties:
            for source, votes in panachage_results[target].items():
                if source in parties or source == '999':
                    election.panachage_results.append(
                        PanachageResult(
                            owner=election.id,
                            id=uuid4(),
                            source=parties.get(source, ''),
                            target=parties[target],
                            votes=votes
                        )
                    )

    return
