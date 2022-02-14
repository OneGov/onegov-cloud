from onegov.election_day.formats.election.internal_proporz import \
    import_election_internal_proporz


def import_election_compound_internal(compound, principal, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.ElectionCompound.export(). This
    is also the format used by onegov.ballot.ProporzElection.export() with
    all exports in one single file.

    Imports as much as possible, skipping elections without relevant data in
    the given file.

    :return:
        A list containing errors.

    """
    errors = []
    for election in compound.elections:
        election_errors = import_election_internal_proporz(
            election, principal, file, mimetype, ignore_extra=True
        )

        if [str(e.error) for e in election_errors] == ['No data found']:
            continue

        for error in election_errors:
            error.filename = election.id

        errors.extend(election_errors)

    return errors
