from onegov.ballot import PartyResult
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv
from sqlalchemy.orm import object_session


def clear_election(election):
    election.counted_entities = 0
    election.total_entities = 0
    election.absolute_majority = None

    session = object_session(election)
    for connection in election.list_connections:
        session.delete(connection)
    for list_ in election.lists:
        session.delete(list_)
    for candidate in election.candidates:
        session.delete(candidate)
    for result in election.results:
        session.delete(result)
    for result in election.party_results:
        session.delete(result)


def parse_party_results_file(file, mimetype, errors):
    party_results = []
    filename = _("Party results")

    # The party results file has one party per line
    if file and mimetype:
        csv, error = load_csv(
            file, mimetype, expected_headers=['Partei', 'Sitze', 'Stimmen'],
            filename=filename
        )
        if error:
            errors.append(error)
        else:
            for line in csv.lines:
                try:
                    name = line.partei or ''
                    mandates = int(line.sitze or 0)
                    votes = int(line.stimmen or 0)
                except ValueError:
                    errors.append(
                        FileImportError(
                            error=_("Invalid values"),
                            line=line.rownumber,
                            filename=filename
                        )
                    )
                else:
                    party_results.append(
                        PartyResult(
                            name=name,
                            votes=votes,
                            number_of_mandates=mandates
                        )
                    )

    return party_results
