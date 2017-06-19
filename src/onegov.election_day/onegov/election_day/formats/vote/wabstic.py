from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.utils import clear_vote


HEADERS_SG_GESCHAEFTE = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    'ausmittlungsstand'
)

HEADERS_SG_GEMEINDEN = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    'sortgemeinde',  # id (BFS)
    'sortgemeindesub',  # id (BFS)
    'sperrung',  # counted
    'stimmberechtigte',   # eligible votes
    'stmungueltig',  # invalid
    'stmleer',  # empty (proposal if simple)
    'stmhgja',  # yeas (proposal)
    'stmhgnein',  # nays (proposal)
    'stmhgohneaw',  # empty (proposal if complex)
    'stmn1ja',  # yeas (counter-proposal)
    'stmn1nein',  # nays (counter-proposal)
    'stmn1ohneaw',  # empty (counter-proposal)
    'stmn2ja',  # yeas (tie-breaker)
    'stmn2nein',  # nays (tie-breaker)
    'stmn2ohneaw',  # empty (tie-breaker)
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


def import_vote_wabstic(vote, entities, district, number,
                        file_sg_geschaefte, mimetype_sg_geschaefte,
                        file_sg_gemeinden, mimetype_sg_gemeinden):
    """ Tries to import the files in the given folder.

    We assume that the file has been generate using WabstiCExport 2.1.

    """
    errors = []

    # Read the files
    sg_geschaefte, error = load_csv(
        file_sg_geschaefte, mimetype_sg_geschaefte,
        expected_headers=HEADERS_SG_GESCHAEFTE,
        filename='sg_geschaefte'
    )
    if error:
        errors.append(error)

    sg_gemeinden, error = load_csv(
        file_sg_gemeinden, mimetype_sg_gemeinden,
        expected_headers=HEADERS_SG_GEMEINDEN,
        filename='sg_gemeinden'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Get the vote type
    used_ballot_types = ['proposal']
    if (vote.meta or {}).get('vote_type', 'simple') == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    # Parse the vote
    complete = 0
    for line in sg_geschaefte.lines:
        line_errors = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue

        try:
            complete = int(line.ausmittlungsstand or 0)
            assert 0 <= complete <= 3
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid values"))

        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='sg_geschaefte'
                )
                for err in line_errors
            )
            continue

    # Parse the results
    ballot_results = {key: [] for key in used_ballot_types}
    added_entities = []
    for line in sg_gemeinden.lines:
        line_errors = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue

        # Parse the id of the entity
        entity_id = None
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
        try:
            counted = False if int(line.sperrung or 0) == 0 else True
        except ValueError:
            line_errors.append(_("Invalid values"))
        else:
            if not counted:
                continue

        # Parse the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))
        else:
            # Ignore the expats if no eligible voters
            if not entity_id and not elegible_voters:
                continue

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
            empty['proposal'] = (
                int(line.stmleer or 0) or int(line.stmhgohneaw or 0)
            )
            empty['counter-proposal'] = int(line.stmn1ohneaw or 0)
            empty['tie-breaker'] = int(line.stmn2ohneaw or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # Pass the line errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='sg_gemeinden'
                )
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

    clear_vote(vote)

    vote.status = 'unknown'
    if complete == 1:
        vote.status = 'interim'
    if complete == 2:
        vote.status = 'final'

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

            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []
