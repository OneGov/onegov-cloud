from onegov.activity import ActivityCollection


def test_add_activity(session, owner):

    collection = ActivityCollection(session)
    collection.add(
        title="Visit the Butcher",
        username=owner.username,
        lead="Come visit the butcher with us and kill your own baby pig",
        text="<h1>Babe was such an overrated movie</h1>",
        tags=('butcher', 'killing', 'blood', 'fun'),
    )

    activity = collection.by_name('visit-the-butcher')
    assert activity.title == "Visit the Butcher"
    assert activity.username == owner.username
    assert activity.lead.startswith("Come visit the butcher")
    assert activity.text.startswith("<h1>Babe was such a")
    assert activity.tags == {'butcher', 'killing', 'blood', 'fun'}


def test_unique_activity(session, owner):

    collection = ActivityCollection(session)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads'

    collection.add("Möped Lads", username=owner.username)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-1'

    collection.add("Möped Lads", username=owner.username)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-2'


def test_activity_pagination(session, owner):

    collection = ActivityCollection(session)

    for i in range(0, 20):
        collection.add(
            title='{:02d}'.format(i),
            username=owner.username
        )

    collection = collection.page_by_index(0)
    assert [a.title for a in collection.batch] == [
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09"
    ]

    collection = collection.page_by_index(1)
    assert [a.title for a in collection.batch] == [
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"
    ]
