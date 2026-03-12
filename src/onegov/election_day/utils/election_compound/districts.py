from __future__ import annotations

from onegov.core.utils import groupbylist
from operator import itemgetter


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.models import Canton
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import ElectionCompoundPart
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest


def get_districts_data(
    compound: ElectionCompound | ElectionCompoundPart,
    principal: Canton | Municipality,
    request: ElectionDayRequest | None = None
) -> JSONObject_ro:
    """ Returns the data used by elections compounds for rendering entities and
    districts maps. """

    entities = principal.entities.get(compound.date.year, {})
    if compound.domain_elections in ('region', 'district'):
        lookup_items = sorted(
            (value.get(compound.domain_elections), key)
            for key, value in entities.items()
        )
        lookup = {
            key: {
                'id': key,
                'entities': [entity for _, entity in items]
            } for key, items in groupbylist(lookup_items, itemgetter(0))
        }
    if compound.domain_elections == 'municipality':
        lookup = {
            value['name']: {
                'id': key,
                'entities': []
            } for key, value in entities.items()
        }
    if not lookup:
        return {}
    return {
        lookup[election.domain_segment]['id']: {
            'entities': lookup[election.domain_segment]['entities'],
            'votes': 0,
            'percentage': 100.0,
            'counted': election.counted,
            'link': request.link(election) if request else '',
            'progress': '{} / {}'.format(*election.progress),
            'mandates': '{} / {}'.format(
                election.allocated_mandates, election.number_of_mandates
            )
        }
        for election in compound.elections
        if election.domain_segment in lookup
    }
