from __future__ import annotations

from onegov.election_day.formats.imports.election.ech import (
    import_elections_ech)
from onegov.election_day.formats.imports.election.internal_majorz import (
    import_election_internal_majorz)
from onegov.election_day.formats.imports.election.internal_proporz import (
    import_election_internal_proporz)
from onegov.election_day.formats.imports.election.wabstic_majorz import (
    import_election_wabstic_majorz)
from onegov.election_day.formats.imports.election.wabstic_proporz import (
    import_election_wabstic_proporz)


__all__ = (
    'import_election_internal_majorz',
    'import_election_internal_proporz',
    'import_election_wabstic_majorz',
    'import_election_wabstic_proporz',
    'import_elections_ech',
)
