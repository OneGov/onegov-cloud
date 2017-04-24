from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats import EXPATS
from onegov.election_day.formats import FileImportError
from onegov.election_day.formats import load_csv
from onegov.election_day.formats.vote import clear_ballot


HEADERS = (
    'Art',  # domain
    'SortWahlkreis',
    'SortGeschaeft',  # vote number
    'SortGemeinde',  # id (BFS)
    'SortGemeindeSub',  # id (BFS)
    'Sperrung',  # counted
    'Stimmberechtigte',   # eligible votes
    'StmUngueltig',  # invalid
    'StmHGJa',  # yeas (proposal)
    'StmHGNein',  # nays (proposal)
    'StmHGOhneAw',  # empty (proposal)
    'StmN1Ja',  # yeas (counter-proposal)
    'StmN1Nein',  # nays (counter-proposal)
    'StmN1OhneAw',  # empty (counter-proposal)
    'StmN2Ja',  # yeas (tie-breaker)
    'StmN2Nein',  # nays (tie-breaker)
    'StmN2OhneAw',  # empty (tie-breaker)
)


def parse_domain(domain):
    if domain == 'Eidg':
        return 'federation'
    if domain == 'Kant':
        return 'canton'
    if domain == 'Gde':
        return 'municipality'
    return None


def line_is_relevant(line, domain, district, number):
    return (
        parse_domain(line.art) == domain and
        line.sortwahlkreis == district and
        line.sortgeschaeft == number
    )


def import_exporter_files(vote, district, number, entities,
                          file, mimetype):
    """ Tries to import the files in the given folder.

    We assume that the file has been generate using WabstiCExport 2.1.

    """
    errors = []

    # Read the file
    results, error = load_csv(file, mimetype, expected_headers=HEADERS)
    if error:
        return [error]

    # Get the vote type
    used_ballot_types = ['proposal']
    if (vote.meta or {}).get('vote_typ', 'simple') == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    # Read the results
    ballot_results = {key: [] for key in used_ballot_types}
    added_entities = []
    for line in results.lines:
        line_errors = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue

        # Parse the id of the entity
        try:
            entity_id = int(line.sortgemeinde or 0)
            sub_entity_id = int(line.sortgemeindesub or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id not in entities:
                if sub_entity_id in entities:
                    entity_id = sub_entity_id
                elif entity_id in EXPATS or sub_entity_id in EXPATS:
                    entity_id = 0

            if entity_id in added_entities:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id}))
            else:
                added_entities.append(entity_id)

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

        # Check if the entity is counted
        counted = True
        if int(line.sperrung) == 0:
            counted = False

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # Parse the invalid votes
        try:
            invalid = int(line.stmungueltig or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # Parse the yeas
        yeas = {}
        try:
            yeas['proposal'] = int(line.stmhgja or 0)
            yeas['counter-proposal'] = int(line.stmn1ja or 0)
            yeas['tie-breaker'] = int(line.stmn2ja or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # Parse the nays
        nays = {}
        try:
            nays['proposal'] = int(line.stmhgnein or 0)
            nays['counter-proposal'] = int(line.stmn1nein or 0)
            nays['tie-breaker'] = int(line.stmn2nein or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # Parse the empty votes
        empty = {}
        try:
            empty['proposal'] = int(line.stmhgohneaw or 0)
            empty['counter-proposal'] = int(line.stmn1ohneaw or 0)
            empty['tie-breaker'] = int(line.stmn2ohneaw or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        entity_id=entity_id,
                        group=entities.get(entity_id, {}).get('name', ''),
                        counted=counted,
                        elegible_voters=elegible_voters,
                        invalid=invalid,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        empty=empty[ballot_type]
                    )
                )

    if errors:
        return errors

    for ballot_type in used_ballot_types:
        # Add the missing entities
        remaining = (
            entities.keys() -
            set(result.entity_id for result in ballot_results[ballot_type])
        )
        for entity_id in remaining:
            ballot_results[ballot_type].append(
                BallotResult(
                    entity_id=entity_id,
                    group=entities.get(entity_id, {}).get('name', ''),
                    counted=False,
                )
            )

        if ballot_results[ballot_type]:
            ballot = next(
                (b for b in vote.ballots if b.type == ballot_type), None
            )
            if not ballot:
                ballot = Ballot(type=ballot_type)
                vote.ballots.append(ballot)

            clear_ballot(ballot)

            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []
