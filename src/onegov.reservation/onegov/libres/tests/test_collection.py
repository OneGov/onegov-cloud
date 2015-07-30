from onegov.libres import ResourceCollection


def test_resource_add(libres_context):

    collection = ResourceCollection(libres_context)
    assert collection.query().count() == 0

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    assert resource.name == 'executive-lounge'
    assert resource.timezone == 'Europe/Zurich'
    assert resource.scheduler.resource == resource.id

    assert collection.query().count() == 1
    assert hasattr(collection.by_id(resource.id), 'scheduler')
    assert hasattr(collection.by_name('executive-lounge'), 'scheduler')
