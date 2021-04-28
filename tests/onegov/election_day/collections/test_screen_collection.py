from onegov.election_day.collections import ScreenCollection
from onegov.election_day.models import Screen


def test_screen_collection(session):
    collection = ScreenCollection(session)
    collection.add(Screen(number=10, type='proporz', structure='<title />'))
    collection.add(Screen(number=12, type='proporz', structure='<title />'))
    collection.add(Screen(number=8, type='proporz', structure='<title />'))
    assert [screen.number for screen in collection.query()] == [8, 10, 12]

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
