import pytest

from datetime import date, datetime
from onegov.form import FormCollection
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
    assert resource.highlights is None

    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2015, 8, 5, 12), datetime(2015, 8, 5, 18))
    allocations = scheduler.allocate(dates)

    resource.highlight_allocations(allocations)

    assert resource.date == date(2015, 8, 5)
    assert resource.highlights == [allocations[0].id]


def test_resource_definitions(libres_context):
    collection = ResourceCollection(libres_context)
    resource = collection.add(
        'Executive Lounge', 'Europe/Zurich',
        form_definition="""
            First Name * = ___
            Last Name * = ___
            E-Mail * = @@@
        """
    )

    form_class = resource.form_definition.form_class
    assert hasattr(form_class, 'first_name')
    assert hasattr(form_class, 'last_name')
    assert hasattr(form_class, 'e_mail')

    forms = FormCollection(collection.session)
    assert forms.definitions.query().count() == 1

    resource.form_definition.definition = """
        X * = ___
        Y * = ___
        E-Mail * = @@@
    """

    form_class = resource.form_definition.form_class
    assert hasattr(form_class, 'x')
    assert hasattr(form_class, 'y')
    assert hasattr(form_class, 'e_mail')

    collection.delete(resource)
    assert forms.definitions.query().count() == 0
