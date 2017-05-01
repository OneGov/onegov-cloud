from sqlalchemy.orm import object_session


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


def clear_vote(vote):
    session = object_session(vote)
    vote.status = None
    for ballot in vote.ballots:
        for result in ballot.results:
            session.delete(result)


def clear_ballot(ballot):
    session = object_session(ballot)
    for result in ballot.results:
        session.delete(result)


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
