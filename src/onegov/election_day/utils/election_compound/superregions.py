from onegov.core.utils import groupbylist


def get_superregions_data(compound, principal):
    """ Returns the data used by elections compounds for rendering entities and
    districts maps. """

    if compound.domain_elections != 'region':
        return {}

    entities = principal.entities.get(compound.date.year, {})
    lookup = sorted([
        (value.get('superregion'), key)
        for key, value in entities.items()
    ])
    lookup = groupbylist(lookup, lambda x: x[0])
    lookup = {
        key: {
            'id': key,
            'entities': [v[1] for v in value]
        } for key, value in lookup
    }

    result = {}
    for election in compound.elections:
        if election.domain_supersegment in lookup:
            key = election.domain_supersegment
            id_ = lookup[key]['id']
            if id_ not in result:
                result[id_] = {
                    'entities': lookup[key]['entities'],
                    'votes': 0,
                    'percentage': 100.0,
                    'counted': election.counted
                }
            result[id_]['counted'] = (
                result[id_]['counted'] and election.counted
            )

    return result
