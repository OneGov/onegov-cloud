from onegov.election_day.formats.election.internal_proporz import \
    import_election_internal_proporz
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError


def import_election_compound_internal(compound, principal, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.ElectionCompound.export(). This
    is also the format used by onegov.ballot.ProporzElection.export() with
    all exports in one single file. Does not support separate expat results.

    Imports as much as possible, skipping elections without relevant data in
    the given file.

    :return:
        A list containing errors.

    """
    errors = []
    updated = []
    expats = False
    for election in compound.elections:
        election_errors = import_election_internal_proporz(
            election, principal, file, mimetype, ignore_extra=True
        )

        if election.results.filter_by(entity_id=0).first():
            expats = True

        if [str(e.error) for e in election_errors] == ['No data found']:
            continue

        updated.append(election)
        errors.extend(election_errors)

    if expats:
        errors.append(
            FileImportError(_(
                'This format does not support separate results for expats'
            ))
        )

    if not errors:
        compound.last_result_change = compound.timestamp()
        for election in updated:
            election.last_result_change = compound.last_result_change

    result = []
    for error in sorted(errors, key=lambda x: (x.line, x.error)):
        if error not in result:
            result.append(error)
    return result
