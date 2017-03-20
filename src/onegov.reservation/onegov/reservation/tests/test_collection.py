import pytest

from datetime import date, datetime
from onegov.reservation import ResourceCollection


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


def test_resource_save_delete(libres_context):
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    assert resource.name == 'executive-lounge'
    assert resource.timezone == 'Europe/Zurich'
    scheduler = resource.get_scheduler(libres_context)

    dates = (datetime(2015, 8, 5, 12), datetime(2015, 8, 5, 18))

    scheduler.allocate(dates)
    scheduler.reserve('info@example.org', dates)

    with pytest.raises(AssertionError):
        collection.delete(resource)

    collection.delete(resource, including_reservations=True)

    assert collection.query().count() == 0
    assert scheduler.managed_reservations().count() == 0
    assert scheduler.managed_reserved_slots().count() == 0
    assert scheduler.managed_allocations().count() == 0


def test_resource_highlight_allocations(libres_context):
    collection = ResourceCollection(libres_context)
    resource = collection.add('Executive Lounge', 'Europe/Zurich')

    assert resource.date is None
    assert resource.highlights_min is None
    assert resource.highlights_max is None

    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2015, 8, 5, 12), datetime(2015, 8, 5, 18))
    allocations = scheduler.allocate(dates)

    resource.highlight_allocations(allocations)

    assert resource.date == date(2015, 8, 5)
    assert resource.highlights_min == allocations[0].id
    assert resource.highlights_min == allocations[-1].id


def test_resource_form_definition(libres_context):
    collection = ResourceCollection(libres_context)

    resource = collection.add(
        title='Executive Lounge',
        timezone='Europe/Zurich',
        definition='Mail *= @@@'
    )
    assert resource.form_class().mail is not None

    resource.definition = None
    assert resource.form_class is None
