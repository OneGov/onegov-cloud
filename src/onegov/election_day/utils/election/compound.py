from onegov.core.utils import groupbylist


def get_districts_data(compound, principal):
    """ Returns the data used by elections compounds for rendering entities and
    districts maps. """

    entities = principal.entities.get(compound.date.year, {})
    if compound.domain_elections in ('region', 'district'):
        lookup = sorted([
            (value.get(compound.domain_elections), key)
            for key, value in entities.items()
        ])
        lookup = groupbylist(lookup, lambda x: x[0])
        lookup = {
            key: {
                'id': key,
                'entities': [v[1] for v in value]
            } for key, value in lookup
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
            'counted': election.counted
        }
        for election in compound.elections
        if election.domain_segment in lookup
    }
