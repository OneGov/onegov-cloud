from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from re import match
from sqlalchemy.orm import object_session

HEADERS = [
    'year',
    'total_votes',
    'name',
    'id',
    'color',
    'mandates',
    'votes',
]


def parse_party_result(line, errors, results, totals, parties, election_year):
    try:
        year = int(line.year or election_year)
        total_votes = int(line.total_votes or 0)
        name = line.name or ''
        id_ = int(line.id or 0)
        color = line.color or (
            '#0571b0' if year == election_year else '#999999'
        )
        mandates = int(line.mandates or 0)
        votes = int(line.votes or 0)
        assert all((year, total_votes, name, color))
        assert match(r'^#[0-9A-Fa-f]{6}$', color)
        assert totals.get(year, total_votes) == total_votes
    except (ValueError, AssertionError):
        errors.append(_("Invalid values"))
    else:
        key = '{}/{}'.format(name, year)
        totals[year] = total_votes
        parties[id_] = name

        if key in results:
            errors.append(_("${name} was found twice", mapping={'name': key}))
        else:
            results[key] = PartyResult(
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
        if header.startswith('panachage_votes_from_'):
            parts = header.split('panachage_votes_from_')
            if len(parts) > 1:
                try:
                    number = int(parts[1])
                    headers[csv.as_valid_identifier(header)] = number
                except ValueError:
                    pass
    return headers


def parse_panachage_results(line, errors, results, headers, election_year):
    try:
        target = int(line.id or 0)
        year = int(line.year or election_year)
        if target not in results and year == election_year:
            results[target] = {}
            for name, index in headers.items():
                results[target][index] = int(getattr(line, name) or 0)

    except ValueError:
        errors.append(_("Invalid values"))


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
    panachage_headers = []

    # The party results file has one party per year per line (but only
    # panachage results in the year of the election)
    if file and mimetype:
        csv, error = load_csv(file, mimetype, expected_headers=HEADERS)
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
                if source in parties or source == 999:
                    election.panachage_results.append(
                        PanachageResult(
                            source=parties.get(source, ''),
                            target=parties[target],
                            votes=votes
                        )
                    )

    return
