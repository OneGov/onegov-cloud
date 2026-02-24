from __future__ import annotations

from onegov.election_day.formats.imports.ech import import_ech
from onegov.election_day.formats.imports.election_compound import (
    import_election_compound_internal)
from onegov.election_day.formats.imports.election import (
    import_election_internal_majorz)
from onegov.election_day.formats.imports.election import (
    import_election_internal_proporz)
from onegov.election_day.formats.imports.election import (
    import_election_wabstic_majorz)
from onegov.election_day.formats.imports.election import (
    import_election_wabstic_proporz)
from onegov.election_day.formats.imports.party_result import (
    import_party_results_internal)
from onegov.election_day.formats.imports.vote import import_vote_internal
from onegov.election_day.formats.imports.vote import import_vote_wabstic


__all__ = (
    'import_ech',
    'import_election_compound_internal',
    'import_election_internal_majorz',
    'import_election_internal_proporz',
    'import_election_wabstic_majorz',
    'import_election_wabstic_proporz',
    'import_party_results_internal',
    'import_vote_internal',
    'import_vote_wabstic',
)
