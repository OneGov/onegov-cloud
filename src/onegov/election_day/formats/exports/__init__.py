from onegov.ballot import Vote
from onegov.election_day.formats.exports.election import \
    export_election_internal
from onegov.election_day.formats.exports.election import \
    export_election_internal_majorz
from onegov.election_day.formats.exports.election import \
    export_election_internal_proporz
from onegov.election_day.formats.exports.election_compound import \
    export_election_compound_internal
from onegov.election_day.formats.exports.party_result import \
    export_parties_internal
from onegov.election_day.formats.exports.vote import export_vote_ech_0252
from onegov.election_day.formats.exports.vote import export_vote_internal


def export_internal(item, locales):
    if isinstance(item, Vote):
        return export_vote_internal(item, locales)
    return export_election_internal(item, locales)


__all__ = [
    'export_election_internal',
    'export_election_internal_majorz',
    'export_election_internal_proporz',
    'export_election_compound_internal',
    'export_internal',
    'export_parties_internal',
    'export_vote_ech_0252',
    'export_vote_internal',
]
