from __future__ import annotations

from onegov.election_day.formats.imports.election.internal_proporz import (
    import_election_internal_proporz)
from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Canton
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import Municipality


def import_election_compound_internal(
    compound: ElectionCompound,
    principal: Canton | Municipality,
    file: IO[bytes],
    mimetype: str
) -> list[FileImportError]:
    """ Tries to import the given file (internal format).

    Does not support separate expat results.

    :return:
        A list containing errors.

    """
    errors: set[FileImportError] = set()
    updated = []
    has_expats = False
    for election in compound.elections:
        election_errors = import_election_internal_proporz(
            election, principal, file, mimetype, ignore_extra=True
        )

        expat_results = [r for r in election.results if r.entity_id == 0]
        if expat_results:
            has_expats = True

        if (
            len(election_errors) == 1
            and str(election_errors[0].error) == 'No data found'
        ):
            continue

        updated.append(election)
        errors.update(
            error
            for error in election_errors
            if str(error.error) != 'No data found'
        )

    if has_expats:
        errors.add(
            FileImportError(_(
                'This format does not support separate results for expats'
            ))
        )

    if not errors:
        compound.last_result_change = compound.timestamp()
        for election in compound.elections:
            if election not in updated:
                election.clear_results(True)
            election.last_result_change = compound.last_result_change

    return sorted(errors, key=lambda x: (x.line or 0, x.error or ''))
