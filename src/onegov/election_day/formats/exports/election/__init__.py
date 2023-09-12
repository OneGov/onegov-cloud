from onegov.election_day.formats.exports.election.internal_majorz import \
    export_election_internal_majorz
from onegov.election_day.formats.exports.election.internal_proporz import \
    export_election_internal_proporz


def export_election_internal(election, locales):
    if election.type == 'proporz':
        return export_election_internal_proporz(election, locales)
    return export_election_internal_majorz(election, locales)


__all__ = [
    'export_election_internal',
    'export_election_internal_majorz',
    'export_election_internal_proporz',
]
