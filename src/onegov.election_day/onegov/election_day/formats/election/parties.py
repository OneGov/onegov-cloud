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
    'color',
    'mandates',
    'votes',
]


def import_party_results(election, file, mimetype):
    """ Tries to import the given file.

    :return:
        A list containing errors.

    """

    errors = []
    party_results = {}
    totals = {}

    # The party results file has one party per line
    if file and mimetype:
        csv, error = load_csv(file, mimetype, expected_headers=HEADERS)
        if error:
            errors.append(error)
        else:
            for line in csv.lines:
                try:
                    year = int(line.year or election.date.year)
                    total_votes = int(line.total_votes or 0)
                    name = line.name or ''
                    color = line.color or (
                        '#0571b0' if year == election.date.year else '#999999'
                    )
                    mandates = int(line.mandates or 0)
                    votes = int(line.votes or 0)
                    assert all((year, total_votes, name, color))
                    assert match(r'^#[0-9A-Fa-f]{6}$', color)
                    assert totals.get(year, total_votes) == total_votes
                except (ValueError, AssertionError):
                    errors.append(
                        FileImportError(
                            error=_("Invalid values"),
                            line=line.rownumber,
                        )
                    )
                else:
                    key = '{}/{}'.format(name, year)
                    totals[year] = total_votes

                    if key in party_results:
                        errors.append(
                            FileImportError(
                                error=_(
                                    "${name} was found twice",
                                    mapping={'name': key}
                                ),
                                line=line.rownumber,
                            )
                        )
                    else:
                        party_results[key] = PartyResult(
                            year=year,
                            total_votes=total_votes,
                            name=name,
                            color=color,
                            number_of_mandates=mandates,
                            votes=votes
                        )

    if errors:
        return errors

    session = object_session(election)
    for result in election.party_results:
        session.delete(result)

    for result in party_results.values():
        election.party_results.append(result)

    return
