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

    tasks = get_tasks([('onegov.core.tests', MyUpgradeModule)])

    assert len(tasks) == 2

    assert tasks[0].task_id \
        == 'onegov.core.tests:Add another field'
    assert tasks[0].task_name == 'Add another field'
    assert tasks[0].always_run is True
    assert tasks[0].requires is None

    assert tasks[1].task_id \
        == 'onegov.core.tests:Add new field'
    assert tasks[1].always_run is False
    assert tasks[1].requires is None


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
