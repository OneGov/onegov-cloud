from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.imports.common import BALLOT_TYPES
from onegov.election_day.formats.imports.common import EXPATS, validate_integer
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.formats.imports.common import load_csv


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Vote
    from onegov.ballot.types import BallotType
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


DEFAULT_VOTE_HEADER = (
    'id',
    'ja stimmen',
    'nein stimmen',
    'Stimmberechtigte',
    'leere stimmzettel',
    'ungültige stimmzettel'
)


def import_vote_default(
    vote: 'Vote',
    principal: 'Canton | Municipality',
    ballot_type: 'BallotType',
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
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
        file, mimetype, expected_headers=DEFAULT_VOTE_HEADER,
        filename=filename
    )
    if error:
        return [error]

    ballot = vote.ballot(ballot_type)

    ballot_results = []
    errors: list[FileImportError] = []
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

    def skip_line(line: 'DefaultRow') -> bool:
        for column in significant_columns:
            if str(getattr(line, column, '')).lower() in skip_indicators:
                return True

        return False

    skipped = 0

    assert csv is not None
    for line in csv.lines:

        if skip_line(line):
            skipped += 1
            continue

        line_errors = []

        # the id of the municipality or district
        entity_id = None
        name = ''
        district = None
        try:
            entity_id = validate_integer(line, 'id')
        except ValueError as e:
            line_errors.append(e.args[0])
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
                name, district, superregion = get_entity_and_district(
                    entity_id, entities, vote, principal, line_errors
                )

            if not line_errors:
                added_entity_ids.add(entity_id)

        # Skip expats if not enabled
        if entity_id == 0 and not vote.has_expats:
            continue

        # the yeas
        try:
            yeas = validate_integer(line, 'ja_stimmen')

        except ValueError as e:
            line_errors.append(e.args[0])

        # the nays
        try:
            nays = validate_integer(line, 'nein_stimmen')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the eligible voters
        try:
            eligible_voters = validate_integer(line, 'stimmberechtigte')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the empty votes
        try:
            empty = validate_integer(line, 'leere_stimmzettel')
        except ValueError as e:
            line_errors.append(e.args[0])

        # the invalid votes
        try:
            invalid = validate_integer(line, 'ungultige_stimmzettel')
        except ValueError as e:
            line_errors.append(e.args[0])

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
            assert entity_id is not None
            ballot_results.append(
                BallotResult(
                    name=name,
                    district=district,
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
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= added_entity_ids
        for entity_id in remaining:
            name, district, superregion = get_entity_and_district(
                entity_id, entities, vote, principal
            )
            if vote.domain == 'municipality':
                if principal.domain != 'municipality':
                    if name != vote.domain_segment:
                        continue
            ballot_results.append(
                BallotResult(
                    name=name,
                    district=district,
                    counted=False,
                    entity_id=entity_id
                )
            )

    if errors:
        return errors

    if ballot_results:
        vote.last_result_change = vote.timestamp()
        vote.status = None
        # todo:
        ballot.clear_results()

        for result in ballot_results:
            ballot.results.append(result)

    return []
