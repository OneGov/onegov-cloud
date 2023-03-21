from onegov.ballot import ElectionCompoundPart


def get_superregions(compound, principal):
    """ Returns all superregions. """

    if compound.domain_elections != 'region':
        return {}

    entities = principal.entities.get(compound.date.year, {})
    result = {entity.get('superregion') for entity in entities.values()}
    result = {
        superregion: {
            'superregion': ElectionCompoundPart(
                compound, 'superregion', superregion
            ),
            'mandates': {'allocated': 0, 'total': 0},
            'progress': {'counted': 0, 'total': 0}
        }
        for superregion in sorted(s for s in result if s)
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


def get_superregions_data(compound, principal, request=None):
    """ Returns the data used by elections compounds for rendering entities and
    districts maps. """

    if compound.domain_elections != 'region':
        return {}

    result = get_superregions(compound, principal)

    for values in result.values():
        values['votes'] = 0
        values['percentage'] = 100.0
        values['counted'] = values['superregion'].counted
        values['progress'] = '{} / {}'.format(
            values['progress']['counted'],
            values['progress']['total']
        )
        values['mandates'] = '{} / {}'.format(
            values['mandates']['allocated'],
            values['mandates']['total']
        )
        values['link'] = request.link(values['superregion']) if request else ''
        del values['superregion']

    entities = principal.entities.get(compound.date.year, {})
    for entity_id, values in entities.items():
        superregion = values.get('superregion')
        if superregion and superregion in result:
            result[superregion].setdefault('entities', [])
            result[superregion]['entities'].append(entity_id)

    return result
