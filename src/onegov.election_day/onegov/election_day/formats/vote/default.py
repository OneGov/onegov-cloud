from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import BALLOT_TYPES


HEADERS = [
    'id',
    'ja stimmen',
    'nein stimmen',
    'Stimmberechtigte',
    'leere stimmzettel',
    'ungültige stimmzettel'
]


def import_vote_default(vote, principal, ballot_type, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file to the given ballot
    result type.

    This is a custom format defined by us to easily create vote results by
    hand.

    :return:
        A list containing errors.

    """
    assert ballot_type in BALLOT_TYPES

    filename = {
        'proposal': _("Proposal"),
        'counter-proposal': _("Counter Proposal"),
        'tie-breaker': _("Tie-Breaker")
    }.get(ballot_type)

    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename
    )
    if error:
        return [error]

    ballot = vote.ballot(ballot_type, create=True)

    ballot_results = []
    errors = []
    added_entity_ids = set()
    entities = principal.entities[vote.date.year]

    # if we have the value "unknown" or "unbekannt" in any of the following
    # colums, we ignore the whole line
    significant_columns = (
        'ja_stimmen',
        'leere_stimmzettel',
        'nein_stimmen',
        'stimmberechtigte',
        'ungultige_stimmzettel',
    )

    skip_indicators = ('unknown', 'unbekannt')

    def skip_line(line):
        for column in significant_columns:
            if str(getattr(line, column, '')).lower() in skip_indicators:
                return True

        return False

    skipped = 0

    for line in csv.lines:

        if skip_line(line):
            skipped += 1
            continue

        line_errors = []

        # the id of the municipality or district
        try:
            entity_id = int(line.id or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id not in entities and entity_id in EXPATS:
                entity_id = 0

            if entity_id in added_entity_ids:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id})
                )

            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id})
                )
            else:
                added_entity_ids.add(entity_id)

        # the yeas
        try:
            yeas = int(line.ja_stimmen or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        try:
            nays = int(line.nein_stimmen or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the eligible voters
        try:
            eligible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the eligible voters"))

        # the empty votes
        try:
            empty = int(line.leere_stimmzettel or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = int(line.ungultige_stimmzettel or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # now let's do some sanity checks
        try:
            if not eligible_voters:
                line_errors.append(_("No eligible voters"))

            if (yeas + nays + empty + invalid) > eligible_voters:
                line_errors.append(_("More cast votes than eligible voters"))

        except UnboundLocalError:
            pass

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename=filename
                )
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            entity = entities.get(entity_id, {})
            ballot_results.append(
                BallotResult(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=True,
                    yeas=yeas,
                    nays=nays,
                    eligible_voters=eligible_voters,
                    entity_id=entity_id,
                    empty=empty,
                    invalid=invalid
                )
            )

    if not errors and not ballot_results and not skipped:
        errors.append(FileImportError(_("No data found")))

    if not errors:
        # Add the missing entities as uncounted results
        for entity_id in (entities.keys() - added_entity_ids):
            entity = entities[entity_id]
            ballot_results.append(
                BallotResult(
                    name=entity.get('name', ''),
                    district=entity.get('district', ''),
                    counted=False,
                    entity_id=entity_id
                )
            )

    if errors:
        return errors

    if ballot_results:
        vote.status = None
        ballot.clear_results()

        for result in ballot_results:
            ballot.results.append(result)

    return []
