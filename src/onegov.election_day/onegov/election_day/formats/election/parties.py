from onegov.ballot import PartyResult
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from sqlalchemy.orm import object_session


def import_party_results(election, file, mimetype):
    """ Tries to import the given file.

    :return:
        A list containing errors.

    """

    party_results = []
    filename = _("Party results")
    errors = []

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

    if errors:
        return errors

    session = object_session(election)
    for result in election.party_results:
        session.delete(result)

    for result in party_results:
        election.party_results.append(result)

    return
