import pytest

from onegov.core.upgrade import get_tasks, upgrade_task


def test_upgrade_task_registration():

    class MyUpgradeModule(object):

        @upgrade_task(name='Add new field')
        def add_new_field(request):
            pass

        @upgrade_task(name='Add another field', always_run=True)
        def add_another_field(request):
            pass

    tasks = get_tasks([('onegov.core', MyUpgradeModule)])

    assert len(tasks) == 2

    assert tasks[0][0] == 'onegov.core:Add another field'
    assert tasks[0][1].task_name == 'Add another field'
    assert tasks[0][1].always_run is True
    assert tasks[0][1].requires is None

    assert tasks[1][0] == 'onegov.core:Add new field'
    assert tasks[1][1].task_name == 'Add new field'
    assert tasks[1][1].always_run is False
    assert tasks[1][1].requires is None


def test_upgrade_task_requirements():

    class Two(object):

        @upgrade_task(name='New Field', requires='one:Init Database')
        def init(request):
            pass

        @upgrade_task(name='Destroy Database', requires='two:New Field')
        def destroy(request):
            pass

    class One(object):

        @upgrade_task(name='Init Database')
        def init(request):
            pass

    tasks = get_tasks([('one', One), ('two', Two)])

    assert len(tasks) == 3

    assert tasks[0][0] == 'one:Init Database'
    assert tasks[1][0] == 'two:New Field'
    assert tasks[2][0] == 'two:Destroy Database'

    assert tasks[0][1].task_name == 'Init Database'
    assert tasks[1][1].task_name == 'New Field'
    assert tasks[2][1].task_name == 'Destroy Database'


def test_upgrade_duplicate_tasks():

    class MyUpgradeModule(object):

        @upgrade_task(name='Add new field')
        def add_new_field(request):
            pass

        @upgrade_task(name='Add new field')
        def add_another_field(request):
            pass

    with pytest.raises(AssertionError):
        get_tasks([('onegov.core.tests', MyUpgradeModule)])
