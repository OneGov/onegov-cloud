from onegov.election_day.collections import ScreenCollection
from onegov.election_day.models import Screen


def test_screen_collection(session):
    collection = ScreenCollection(session)
    collection.add(
        Screen(
            number=10,
            type='proporz_election',
            structure='<h1><title /></h1>',
            css='h1 { font-weight: normal; }'
        )
    )
    collection.add(
        Screen(
            number=12,
            type='simple_vote',
            structure='<text>Hi!</text>',
            duration=10,
            group='XYZ'
        )
    )
    collection.add(
        Screen(
            number=8,
            type='mamorz_election',
            structure='Lorem ipsum',
            description='Lorem lorem ipsum ipsum'
        )
    )
    assert [screen.number for screen in collection.query()] == [8, 10, 12]

    assert collection.export() == [
        {
            'css': None,
            'description': 'Lorem lorem ipsum ipsum',
            'duration': None,
            'group': None,
            'number': 8,
            'structure': 'Lorem ipsum',
            'type': 'mamorz_election'
        },
        {
            'css': 'h1 { font-weight: normal; }',
            'description': None,
            'duration': None,
            'group': None,
            'number': 10,
            'structure': '<h1><title /></h1>',
            'type': 'proporz_election'
        },
        {
            'css': None,
            'description': None,
            'duration': 10,
            'group': 'XYZ',
            'number': 12,
            'structure': '<text>Hi!</text>',
            'type': 'simple_vote'
        }
    ]

    screen = collection.by_number(10)
    assert screen == collection.by_id(screen.id)
    collection.delete(screen)

    assert [screen.number for screen in collection.query()] == [8, 12]


def test_screen_collection_pagination(session):
    collection = ScreenCollection(session)

    for number in range(100):
        collection.add(
            Screen(
                number=number,
                type='proporz',
                structure='<title />'
            )
        )
    assert collection.query().count() == 100

    assert ScreenCollection(session, page=0).batch[0].number == 0
    assert ScreenCollection(session, page=4).batch[4].number == 44
    assert ScreenCollection(session, page=5).batch[5].number == 55
    assert ScreenCollection(session, page=9).batch[9].number == 99

    assert len(ScreenCollection(session, page=10).batch) == 0
