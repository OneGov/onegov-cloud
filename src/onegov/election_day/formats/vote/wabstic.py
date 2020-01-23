from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS, validate_integer
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from sqlalchemy.orm import object_session

from onegov.election_day.import_export.mappings import \
    WABSTIC_VOTE_HEADERS_SG_GESCHAEFTE, WABSTIC_VOTE_HEADERS_SG_GEMEINDEN


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
        parse_domain(line.art) == domain
        and line.sortwahlkreis == district
        and line.sortgeschaeft == number
    )


def import_vote_wabstic(vote, principal, number, district,
                        file_sg_geschaefte, mimetype_sg_geschaefte,
                        file_sg_gemeinden, mimetype_sg_gemeinden):
    """ Tries to import the given CSV files from a WabstiCExport.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """
    errors = []
    entities = principal.entities[vote.date.year]

    # Read the files
    sg_geschaefte, error = load_csv(
        file_sg_geschaefte, mimetype_sg_geschaefte,
        expected_headers=WABSTIC_VOTE_HEADERS_SG_GESCHAEFTE,
        filename='sg_geschaefte'
    )
    if error:
        errors.append(error)

    sg_gemeinden, error = load_csv(
        file_sg_gemeinden, mimetype_sg_gemeinden,
        expected_headers=WABSTIC_VOTE_HEADERS_SG_GEMEINDEN,
        filename='sg_gemeinden'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Get the vote type
    used_ballot_types = ['proposal']
    if vote.type == 'complex':
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    # Parse the vote
    remaining_entities = None
    ausmittlungsstand = None
    for line in sg_geschaefte.lines:
        line_errors = []

        if not line_is_relevant(line, vote.domain, district, number):
            continue
        try:
            ausmittlungsstand = validate_integer(line, 'ausmittlungsstand')
            assert 0 <= ausmittlungsstand <= 3

        except ValueError as e:
            line_errors.append(e.args[0])
        except AssertionError:
            line_errors.append(
                _("Value of ausmittlungsstand not between 0 and 3"))

        remaining_entities = None
        try:
            remaining_entities = validate_integer(
                line, 'anzgdependent', default=None)
        except AttributeError:
            # the row is not in the files and ausmittlungsstand precedes
            pass
        except Exception as e:
            line_errors.append(
                _("Error in anzgdependent: ${msg}",
                  mapping={'msg': e.args[0]}))

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
            entity_id = validate_integer(line, 'bfsnrgemeinde')
        except ValueError as e:
            line_errors.append(e.args[0])
        else:
            entity_id = 0 if entity_id in EXPATS else entity_id

            if entity_id in added_entities:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id}))
            else:
                added_entities.append(entity_id)

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

        # Skip expats if not enabled
        if entity_id == 0 and not vote.expats:
            continue

        # Check if the entity is counted
        try:
            counted_num = validate_integer(line, 'sperrung')
            counted = False if counted_num == 0 else True
        except ValueError:
            line_errors.append(_("Invalid values"))
        else:
            if not counted:
                continue

        # Parse the eligible voters
        try:
            eligible_voters = validate_integer(line, 'stimmberechtigte')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the invalid votes
        try:
            invalid = validate_integer(line, 'stmungueltig')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the yeas
        yeas = {}
        try:
            yeas['proposal'] = validate_integer(line, 'stmhgja')
            yeas['counter-proposal'] = validate_integer(line, 'stmn1ja')
            yeas['tie-breaker'] = validate_integer(line, 'stmn2ja')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the nays
        nays = {}
        try:
            nays['proposal'] = validate_integer(line, 'stmhgnein')
            nays['counter-proposal'] = validate_integer(line, 'stmn1nein')
            nays['tie-breaker'] = validate_integer(line, 'stmn2nein')
        except ValueError as e:
            line_errors.append(e.args[0])

        # Parse the empty votes
        empty = {}
        try:
            empty['proposal'] = (
                validate_integer(line, 'stmleer')
                or validate_integer(line, 'stmhgohneaw')
            )
            empty['counter-proposal'] = validate_integer(line, 'stmn1ohneaw')
            empty['tie-breaker'] = validate_integer(line, 'stmn2ohneaw')
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
                entity = entities.get(entity_id, {})
                ballot_results[ballot_type].append(
                    dict(
                        entity_id=entity_id,
                        name=entity.get('name', ''),
                        district=entity.get('district', ''),
                        counted=counted,
                        eligible_voters=eligible_voters,
                        invalid=invalid,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        empty=empty[ballot_type]
                    )
                )

    if errors:
        return errors

    # Add the missing entities
    for ballot_type in used_ballot_types:
        remaining = set(entities.keys())
        if vote.expats:
            remaining.add(0)
        remaining -= set(r['entity_id'] for r in ballot_results[ballot_type])
        for entity_id in remaining:
            entity = entities.get(entity_id, {})
            ballot_results[ballot_type].append(
                dict(
                    entity_id=entity_id,
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=False,
                )
            )

    # Add the results to the DB
    vote.clear_results()
    vote.status = 'unknown'

    def decide_vote_status(remaining_entities, ausmittlungsstand):
        """

        :param remaining_entities: precedes ausmittlungstand for status
        :param ausmittlungsstand: value between 0 and 3
        :return:
        """

        # If all the lines were skipped
        if remaining_entities is None and ausmittlungsstand is None:
            return 'unknown'

        if remaining_entities is not None:
            if remaining_entities == 0:
                return 'final'
            else:
                return 'interim'

        elif ausmittlungsstand == 1:
            return 'interim'
        elif ausmittlungsstand == 0:
            return 'unknown'
        raise ValueError

    vote.status = decide_vote_status(remaining_entities, ausmittlungsstand)

    ballot_ids = {b: vote.ballot(b, create=True).id for b in used_ballot_types}

    session = object_session(vote)
    session.flush()
    session.bulk_insert_mappings(
        BallotResult,
        (
            dict(**result, ballot_id=ballot_ids[ballot_type])
            for ballot_type in used_ballot_types
            for result in ballot_results[ballot_type]
        )
    )

    return []
