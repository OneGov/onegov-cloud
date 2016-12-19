from onegov.election_day.formats.election.wabsti.majorz import (
    import_file as import_wabsti_file_majorz
)
from onegov.election_day.formats.election.wabsti.proporz import (
    import_file as import_wabsti_file_proporz
)


def import_file(municipalities, election, file, mimetype,
                connections_file=None, connections_mimetype=None,
                elected_file=None, elected_mimetype=None,
                statistics_file=None, statistics_mimetype=None,
                parties_file=None, parties_mimetype=None):
    """ Tries to import the given file (wabsti format).

    :return: A dictionary containing the status and a list of errors if any.
    For example::

        {'status': 'ok', 'errors': []}
        {'status': 'error': 'errors': ['x on line y is z']}

    """

    if election.type == 'majorz':
        return import_wabsti_file_majorz(
            municipalities, election, file, mimetype,
            elected_file, elected_mimetype
        )
    else:
        return import_wabsti_file_proporz(
            municipalities, election, file, mimetype,
            connections_file, connections_mimetype,
            elected_file, elected_mimetype,
            statistics_file, statistics_mimetype,
            parties_file, parties_mimetype
        )
