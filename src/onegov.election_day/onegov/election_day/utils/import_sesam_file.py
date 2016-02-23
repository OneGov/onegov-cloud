from onegov.ballot import CandidateResult, ElectionResult, ListResult
from onegov.election_day import _
from onegov.election_day.utils import FileImportError, load_csv
from sqlalchemy.orm import object_session


HEADERS_COMMON = [
    # Municipality
    'Anzahl Sitze',
    'Wahlkreis-Nr',
    'Stimmberechtigte',
    'Wahlzettel',
    'Ungültige Wahlzettel',
    'Leere Wahlzettel',
    'Leere Stimmen',
    # Candidate
    'Kandidaten-Nr',
    'Name',
    'Vorname',
    'Anzahl Gemeinden',
]

HEADERS_MAJORZ = [
    # Municipality
    'Ungueltige Stimmen',
    # Candidate
    'Stimmen',
]

HEADERS_PROPORZ = [
    # List
    'Listen-Nr',
    'Partei-ID',
    'Parteikurzbezeichnung',
    'Parteibezeichnung',
    'HLV-Nr',
    'HLV-Bezeichnung',
    'ULV-Nr',
    'ULV-Bezeichnung',
    'Anzahl Sitze Liste',
    'Unveränderte Wahlzettel Liste',
    'Veränderte Wahlzettel Liste',
    'Kandidatenstimmen unveränderte Wahlzettel',
    'Zusatzstimmen unveränderte Wahlzettel',
    'Kandidatenstimmen veränderte Wahlzettel',
    'Zusatzstimmen veränderte Wahlzettel',
    # Candidate
    'Gewählt',
    'Stimmen unveränderte Wahlzettel',
    'Stimmen veränderte Wahlzettel',
    'Stimmen Total aus Wahlzettel',
]


def parse_common(line, values, errors):
    # the id of the municipality
    values['municipality_id'] = None
    try:
        values['municipality_id'] = int(line.wahlkreis_nr or 0)
    except ValueError:
        errors.append(_("Invalid municipality id"))

    # the number of mandates
    values['number_of_mandates'] = int(line.anzahl_sitze or 0)
    if not values['number_of_mandates']:
        errors.append(_("No number of mandates"))

    # counted municipalities
    numbers = line.anzahl_gemeinden.split(' von ')
    if not len(numbers) == 2:
        errors.append(_("Invalid number of counted municipalities"))
    else:
        values['counted'] = int(numbers[0])
        values['total'] = int(numbers[1])

    # number of elegible voters
    values['elegible_voters'] = int(line.stimmberechtigte or 0)
    if not values['elegible_voters']:
        errors.append(_("No elegible voters"))

    # number of received ballots
    values['received_ballots'] = int(line.wahlzettel or 0)

    # number of blank ballots
    values['blank_ballots'] = int(line.leere_wahlzettel or 0)

    # number of invalid ballots
    values['invalid_ballots'] = int(line.ungultige_wahlzettel or 0)

    # number of blank votes
    values['blank_votes'] = int(line.leere_stimmen or 0)

    # the id of the candidate
    try:
        values['candidate_id'] = int(line.kandidaten_nr or 0)
    except ValueError:
        errors.append(_("Invalid candidate id"))

    # elected
    try:
        values['elected'] = line.gewaehlt == 'Gewaehlt'
    except AttributeError:
        values['elected'] = line.gewahlt == 'Gewählt'

    # the family name
    values['family_name'] = line.name

    # the first name
    values['first_name'] = line.vorname


def parse_majorz(line, values, errors):
    # number of invalid votes
    values['invalid_votes'] = int(line.ungueltige_stimmen or 0)

    # votes
    values['candidate_votes'] = int(line.stimmen or 0)


def parse_proporz(line, values, errors):
    # votes: invalid
    values['invalid_votes'] = 0

    # the id of the list
    values['list_id'] = None
    try:
        values['list_id'] = int(line.listen_nr or 0)
    except ValueError:
        errors.append(_("Invalid list id"))

    # name of the list
    values['list_name'] = line.parteibezeichnung

    # number of mandates the list got
    values['list_nr_of_mandates'] = int(line.anzahl_sitze_liste or 0)

    # number of votes the list got
    values['list_votes'] = (
        int(line.kandidatenstimmen_unveranderte_wahlzettel or 0) +
        int(line.kandidatenstimmen_veranderte_wahlzettel or 0) +
        int(line.zusatzstimmen_unveranderte_wahlzettel or 0) +
        int(line.zusatzstimmen_veranderte_wahlzettel or 0)
    )

    # list connections
    values['list_connection_nr'] = line.hlv_nr
    values['list_connection_description'] = line.hlv_bezeichnung
    values['list_subconnection_nr'] = line.ulv_nr
    values['list_subconnection_description'] = line.ulv_bezeichnung

    # number of the votes the candidate got
    values['candidate_votes'] = int(line.stimmen_total_aus_wahlzettel or 0)


def import_file(municipalities, election, file, mimetype):
    """ Tries to import the given file (sesam format).

    :return: A dictionary containing the status and a list of errors if any.
    For example::

        {'status': 'ok', 'errors': []}
        {'status': 'error': 'errors': ['x on line y is z']}

    """
    majorz = False
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_PROPORZ
    )
    if error and "Missing columns" in error.error:
        majorz = True
        csv, error = load_csv(
            file, mimetype, expected_headers=HEADERS_COMMON + HEADERS_MAJORZ
        )
    type_matches = (
        (majorz and election.type == 'majorz') or
        (not majorz and election.type == 'proporz')
    )
    if not type_matches:
        error = FileImportError(_(
            "The type of the file does not match the type of the election."
        ))
    if error:
        return {'status': 'error', 'errors': [error]}

    errors = []
    results = {}
    lists = {}
    added_candidates = []

    # This format has one candiate per municipality per line
    for line in csv.lines:
        line_errors = []
        values = {}

        parse_common(line, values, line_errors)

        if majorz:
            parse_majorz(line, values, line_errors)
        else:
            parse_proporz(line, values, line_errors)

        mid = values['municipality_id']
        cid = values['candidate_id']
        lid = values['list_id'] if not majorz else None

        # now let's do some sanity checks
        try:
            if mid and mid not in municipalities:
                line_errors.append(
                    _(
                        "municipality id ${id} is unknown",
                        mapping={'id': mid}
                    )
                )

            if mid and cid:
                if (mid, cid) in added_candidates:
                    line_errors.append(
                        _(
                            "candidate id {$cid} for municipality id ${mid} "
                            "was found twice",
                            mapping={
                                'cid': cid,
                                'mid': mid
                            }
                        )
                    )

            if values['received_ballots'] > values['elegible_voters']:
                line_errors.append(
                    _("More received ballots than elegible voters")
                )

            if values['blank_ballots'] > values['elegible_voters']:
                line_errors.append(
                    _("More blank ballots than elegible voters")
                )

            if mid and mid in results:
                existing = results[values['municipality_id']]
                differs = (
                    existing.elegible_voters != values['elegible_voters'] or
                    existing.received_ballots != values['received_ballots'] or
                    existing.blank_ballots != values['blank_ballots'] or
                    existing.invalid_ballots != values['invalid_ballots']
                )
                if differs:
                    line_errors.append(
                        _(
                            "Conflicting values for municipality id ${id}",
                            mapping={'id': values['municipality_id']}
                        )
                    )

            if not majorz and mid and lid and (mid, lid) in lists:
                existing = lists[(mid, lid)]
                differs = (
                    existing.name != values['list_name'] or
                    existing.number_of_mandates != values[
                        'list_nr_of_mandates'
                    ] or
                    existing.list_connection_id != values[
                        'list_connection_nr'
                    ] or
                    existing.list_connection_description != values[
                        'list_connection_description'
                    ] or
                    existing.list_subconnection_id != values[
                        'list_subconnection_nr'
                    ] or
                    existing.list_subconnection_description != values[
                        'list_subconnection_description'
                    ] or
                    existing.votes != values['list_votes']
                )
                if differs:
                    line_errors.append(
                        _(
                            "Conflicting values for municipality id ${id} "
                            "and list id {lid}",
                            mapping={
                                'id': values['municipality_id'],
                                'lid': values['list_id']
                            }
                        )
                    )

            if not values['family_name'] or not values['first_name']:
                line_errors.append(
                    _(
                        "Missing name(s) for candidate ${id}",
                        mapping={'id': values['candidate_id']}
                    )
                )

            if values['invalid_ballots'] > values['elegible_voters']:
                line_errors.append(
                    _("More invalid ballots than elegible voters")
                )

        except UnboundLocalError:
            pass

        added_candidates.append((mid, cid))
        if not majorz and mid and lid and (mid, lid) not in lists:
            lists[(mid, lid)] = ListResult(
                list_id=values['list_id'],
                name=values['list_name'],
                votes=values['list_votes'],
                number_of_mandates=values['list_nr_of_mandates'],
                list_connection_id=values['list_connection_nr'],
                list_connection_description=values[
                    'list_connection_description'
                ],
                list_subconnection_id=values['list_subconnection_nr'],
                list_subconnection_description=values[
                    'list_subconnection_description'
                ],
                group=values['list_id']
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
            if mid not in results:
                results[mid] = ElectionResult(
                    municipality_id=values['municipality_id'],
                    elegible_voters=values['elegible_voters'],
                    received_ballots=values['received_ballots'],
                    blank_ballots=values['blank_ballots'],
                    invalid_ballots=values['invalid_ballots'],
                    blank_votes=values['blank_votes'],
                    invalid_votes=values['invalid_votes'],
                    group=municipalities[mid]['name']
                )

            if not majorz and (mid, lid) in lists:
                results[mid].lists.append(lists[(mid, lid)])

            results[mid].candidates.append(
                CandidateResult(
                    elected=values['elected'],
                    candidate_id=values['candidate_id'],
                    family_name=values['family_name'],
                    first_name=values['first_name'],
                    votes=values['candidate_votes'],
                    list_id=values['list_id'] if not majorz else None,
                    list_name=values['list_name'] if not majorz else None,
                    group=values['candidate_id'],
                )
            )

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    if errors:
        return {'status': 'error', 'errors': errors}

    if results:
        election.number_of_mandates = values['number_of_mandates']
        election.counted_municipalities = values['counted']
        election.total_municipalities = values['total']
        session = object_session(election)
        for result in election.results:
            session.delete(result)
        for result in results:
            election.results.append(results[result])

    return {'status': 'ok', 'errors': errors}
