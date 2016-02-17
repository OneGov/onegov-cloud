from onegov.ballot import CandidateResult, ElectionResult
from onegov.election_day import _
from onegov.election_day.utils import FileImportError, load_csv
from sqlalchemy.orm import object_session


def import_file(municipalities, election, file, mimetype):
    csv, error = load_csv(file, mimetype, expected_headers=[
        'AnzMandate',
        'BFS',
        'StimmBer',
        'StimmAbgegeben',
        'StimmLeer',
        'StimmUngueltig',
        'StimmGueltig',
    ])

    if error:
        return {'status': 'error', 'errors': [error]}

    errors = []
    results = {}
    added_muncipalities = []

    # This format has one municipality per line and every candidate as row
    for line in csv.lines:
        line_errors = []
        candidates = []

        # the id of the municipality
        municipality_id = None
        try:
            municipality_id = int(line.bfs or 0)
        except ValueError:
            line_errors.append(_("Invalid municipality id"))
        else:
            if municipality_id not in municipalities:
                line_errors.append(
                    _(
                        "municipality id ${id} is unknown",
                        mapping={'id': municipality_id}
                    )
                )
            if municipality_id in added_muncipalities:
                line_errors.append(
                    _(
                        "municipality id ${id} found twice",
                        mapping={'id': municipality_id}
                    )
                )
                added_muncipalities.append(municipality_id)

        # the number of mandates
        number_of_mandates = int(line.anzmandate or 0)
        if not number_of_mandates:
            line_errors.append(_("No number of mandates"))

        # todo: we are missing this informations
        # counted municipalities
        # numbers = line.anzahl_gemeinden.split(' von ')
        # if not len(numbers) == 2:
        #     line_errors.append(_("Invalid number of counted municipalities"))
        # else:
        #     counted = int(numbers[0])
        #     total = int(numbers[1])

        # number of elegible voters
        elegible_voters = int(line.stimmber or 0)
        if not elegible_voters:
            line_errors.append(_("No elegible voters"))

        # number of received ballots
        received_ballots = int(line.stimmabgegeben or 0)

        # number of blank ballots
        blank_ballots = int(line.stimmleer or 0)

        # number of invalid ballots
        invalid_ballots = int(line.stimmungueltig or 0)

        # now let's do some sanity checks
        try:
            if received_ballots > elegible_voters:
                line_errors.append(
                    _("More received ballots than elegible voters")
                )
            if blank_ballots > elegible_voters:
                line_errors.append(
                    _("More blank ballots than elegible voters")
                )
            if invalid_ballots > elegible_voters:
                line_errors.append(
                    _("More invalid ballots than elegible voters")
                )

        except UnboundLocalError:
            pass

        count = 0
        while True:
            count += 1
            try:
                # the id of the candidate
                candidate_id = getattr(line, 'kandid_{}'.format(count))
            except AttributeError:
                break
            except ValueError:
                line_errors.append(_("Invalid candidate id"))
            else:
                # the family name
                family_name = getattr(line, 'kandname_{}'.format(count))

                # the first name
                first_name = getattr(line, 'kandvorname_{}'.format(count))

                # votes
                votes = int(getattr(line, 'stimmen_{}'.format(count)) or 0)

                # todo: we are missing this information
                # elected = False

                if family_name == 'Vereinzelte':
                    continue

                elif family_name == 'Leere Zeilen':
                    # number of blank votes
                    blank_votes = votes
                    continue

                elif family_name == 'Ungültige Stimmen':
                    # number of invalid votes
                    invalid_votes = votes
                    continue

                elif not family_name or not first_name:
                    line_errors.append(
                        _(
                            "Missing name(s) for candidate ${id}",
                            mapping={'id': candidate_id}
                        )
                    )

                candidates.append(
                    CandidateResult(
                        # elected=elected,
                        candidate_id=candidate_id,
                        family_name=family_name,
                        first_name=first_name,
                        votes=votes,
                        group='{} {}'.format(family_name, first_name),
                    )
                )

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            if municipality_id not in results:
                results[municipality_id] = ElectionResult(
                    municipality_id=municipality_id,
                    elegible_voters=elegible_voters,
                    received_ballots=received_ballots,
                    blank_ballots=blank_ballots,
                    invalid_ballots=invalid_ballots,
                    blank_votes=blank_votes,
                    invalid_votes=invalid_votes,
                    group=municipalities[municipality_id]['name']
                )
            for candidate in candidates:
                results[municipality_id].candidates.append(candidate)

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return {'status': 'error', 'errors': errors}

    if results:
        election.number_of_mandates = number_of_mandates
        # election.counted_municipalities = counted
        # election.total_municipalities = total
        session = object_session(election)
        for result in election.results:
            session.delete(result)
        for result in results:
            election.results.append(results[result])

    return {'status': 'ok', 'errors': errors}
