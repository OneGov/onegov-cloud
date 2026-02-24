from __future__ import annotations

from onegov.election_day.models import ElectionCompoundPart


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSONObject
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.models import Canton
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest
    from typing import TypedDict

    class SuperregionInfo(TypedDict):
        superregion: ElectionCompoundPart
        mandates: dict[str, int]
        progress: dict[str, int]


def get_superregions(
    compound: ElectionCompound,
    principal: Canton | Municipality
) -> dict[str, SuperregionInfo]:
    """ Returns all superregions. """

    if compound.domain_elections != 'region':
        return {}

    entities = principal.entities.get(compound.date.year, {})
    superregions = {
        superregion
        for entity in entities.values()
        if (superregion := entity.get('superregion'))
    }
    result: dict[str, SuperregionInfo] = {
        superregion: {
            'superregion': ElectionCompoundPart(
                compound, 'superregion', superregion
            ),
            'mandates': {'allocated': 0, 'total': 0},
            'progress': {'counted': 0, 'total': 0}
        }
        for superregion in sorted(superregions)
    }

    keys = set()
    for election in compound.elections:
        if election.domain_supersegment in result:
            key = election.domain_supersegment
            keys.add(key)
            result[key]['progress']['counted'] += 1 if election.counted else 0
            result[key]['progress']['total'] += 1
            result[key]['mandates']['allocated'] += election.allocated_mandates
            result[key]['mandates']['total'] += election.number_of_mandates

    return {k: v for k, v in result.items() if k in keys}


def get_superregions_data(
    compound: ElectionCompound,
    principal: Canton | Municipality,
    request: ElectionDayRequest | None = None
) -> JSONObject_ro:
    """ Returns the data used by elections compounds for rendering entities and
    districts maps. """

    if compound.domain_elections != 'region':
        return {}

    result: dict[str, JSONObject] = {
        key: {
            'votes': 0,
            'percentage': 100.0,
            'counted': values['superregion'].counted,
            'progress': '{} / {}'.format(
                values['progress']['counted'],
                values['progress']['total']
            ),
            'mandates': '{} / {}'.format(
                values['mandates']['allocated'],
                values['mandates']['total']
            ),
            'link': request.link(values['superregion']) if request else '',
        }
        for key, values in get_superregions(compound, principal).items()
    }

    entities = principal.entities.get(compound.date.year, {})
    for entity_id, values in entities.items():
        superregion = values.get('superregion')
        if superregion and superregion in result:
            my_entities = result[superregion].setdefault('entities', [])
            my_entities.append(entity_id)  # type:ignore[union-attr]

    return result
