from onegov.activity import ActivityCollection


def test_add_activity(session, owner):

    collection = ActivityCollection(session)
    collection.add(
        title="Visit the Butcher",
        user=owner,
        lead="Come visit the butcher with us and kill your own baby pig",
        text="<h1>Babe was such an overrated movie</h1>",
        tags=('butcher', 'killing', 'blood', 'fun'),
    )

    activity = collection.by_name('visit-the-butcher')
    assert activity.title == "Visit the Butcher"
    assert activity.user_id == owner.id
    assert activity.lead.startswith("Come visit the butcher")
    assert activity.text.startswith("<h1>Babe was such a")
    assert activity.tags == {'butcher', 'killing', 'blood', 'fun'}


def test_unique_activity(session, owner):

    collection = ActivityCollection(session)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads'

    collection.add("Möped Lads", user=owner)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-1'

    collection.add("Möped Lads", user=owner)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-2'
