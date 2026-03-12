from __future__ import annotations

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
from onegov.election_day.formats.exports.vote import export_vote_internal
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection


def export_internal(
    item: Election | ElectionCompound | Vote,
    locales: Collection[str]
) -> list[dict[str, Any]]:

    if isinstance(item, Vote):
        return export_vote_internal(item, locales)

    if isinstance(item, ElectionCompound):
        return export_election_compound_internal(item, locales)

    if isinstance(item, Election):
        return export_election_internal(item, locales)


__all__ = (
    'export_election_internal',
    'export_election_internal_majorz',
    'export_election_internal_proporz',
    'export_election_compound_internal',
    'export_internal',
    'export_parties_internal',
    'export_vote_internal',
)
