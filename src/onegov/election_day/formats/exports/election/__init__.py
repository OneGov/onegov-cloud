from __future__ import annotations

from onegov.election_day.formats.exports.election.internal_majorz import \
    export_election_internal_majorz
from onegov.election_day.formats.exports.election.internal_proporz import \
    export_election_internal_proporz


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.models import Election


def export_election_internal(
    election: Election,
    locales: Collection[str]
) -> list[dict[str, Any]]:

    if election.type == 'proporz':
        return export_election_internal_proporz(election, locales)
    return export_election_internal_majorz(election, locales)


__all__ = (
    'export_election_internal',
    'export_election_internal_majorz',
    'export_election_internal_proporz',
)
