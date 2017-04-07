BALLOT_TYPES = {'proposal', 'counter-proposal', 'tie-breaker'}

HEADERS = [
    'Bezirk',
    'ID',
    'Name',
    'Ja Stimmen',
    'Nein Stimmen',
    'Stimmberechtigte',
    'Leere Stimmzettel',
    'Ungültige Stimmzettel'
]


def guessed_group(entity, other):
    result = entity['name']

    if other:
        if '/' in other[0].group:
            result = '/'.join(
                p for p in (
                    entity.get('district'),
                    entity.get('name')
                ) if p is not None
            )

    return result
