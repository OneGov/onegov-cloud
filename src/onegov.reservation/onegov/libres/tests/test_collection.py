from onegov.libres import ResourceCollection


def test_resource_collection(libres_context):

    collection = ResourceCollection(libres_context)
    assert collection.query().count() == 0

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    assert resource.name == 'executive-lounge'
    assert resource.timezone == 'Europe/Zurich'
    assert resource.get_scheduler(libres_context).resource == resource.id

    assert collection.query().count() == 1
    assert collection.by_id(resource.id)
    assert collection.by_name('executive-lounge')

    collection.delete(collection.by_id(resource.id))

    assert collection.query().count() == 0
