from onegov.election_day.formats.imports.election.internal_proporz import \
    import_election_internal_proporz
from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError


def import_election_compound_internal(compound, principal, file, mimetype):
    """ Tries to import the given file (internal format).

    Does not support separate expat results.

    :return:
        A list containing errors.

    """
    errors = []
    updated = []
    has_expats = False
    for election in compound.elections:
        election_errors = import_election_internal_proporz(
            election, principal, file, mimetype, ignore_extra=True
        )

        if election.results.filter_by(entity_id=0).first():
            has_expats = True

        if [str(e.error) for e in election_errors] == ['No data found']:
            continue

        election_errors = [
            e for e in election_errors if str(e.error) != 'No data found'
        ]

        updated.append(election)
        errors.extend(election_errors)

    if has_expats:
        errors.append(
            FileImportError(_(
                'This format does not support separate results for expats'
            ))
        )

    if not errors:
        compound.last_result_change = compound.timestamp()
        for election in compound.elections:
            if election not in updated:
                election.clear_results()
            election.last_result_change = compound.last_result_change

    result = []
    for error in sorted(errors, key=lambda x: (x.line or 0, x.error or '')):
        if error not in result:
            result.append(error)
    return result
