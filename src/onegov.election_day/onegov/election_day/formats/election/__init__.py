from onegov.ballot import PartyResult
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv


def parse_party_results_file(file, mimetype, errors):
    party_results = []

    # The party results file has one party per line
    if file and mimetype:
        csv, error = load_csv(
            file, mimetype, expected_headers=['Partei', 'Sitze', 'Stimmen']
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
                            line=line.rownumber
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
