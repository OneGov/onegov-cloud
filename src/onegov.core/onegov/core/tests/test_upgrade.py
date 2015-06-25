import pytest

from onegov.core.upgrade import UpgradeRunner, upgrade_task


def test_upgrade_task_registration():

    class MyUpgradeModule(object):

        @upgrade_task(name='Add new field')
        def add_new_field(request):
            pass

        @upgrade_task(name='Add another field', always_run=True)
        def add_another_field(request):
            pass

    runner = UpgradeRunner(
        upgrade_modules=[('onegov.core.tests', MyUpgradeModule)])

    assert len(runner.upgrade_tasks) == 2

    assert runner.upgrade_tasks[0].task_id \
        == 'onegov.core.tests:Add another field'
    assert runner.upgrade_tasks[0].task_name == 'Add another field'
    assert runner.upgrade_tasks[0].always_run is True
    assert runner.upgrade_tasks[0].requires is None

    assert runner.upgrade_tasks[1].task_id \
        == 'onegov.core.tests:Add new field'
    assert runner.upgrade_tasks[1].always_run is False
    assert runner.upgrade_tasks[1].requires is None


def test_upgrade_duplicate_tasks():

    class MyUpgradeModule(object):

        @upgrade_task(name='Add new field')
        def add_new_field(request):
            pass

        @upgrade_task(name='Add new field')
        def add_another_field(request):
            pass

    with pytest.raises(AssertionError):
        UpgradeRunner(upgrade_modules=[('onegov.core.tests', MyUpgradeModule)])
