import os.path
import pytest
import textwrap

from click.testing import CliRunner
from mock import patch
from onegov.core.cli import cli
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


def test_upgrade_cli(postgres_dsn, session_manager, temporary_directory):

    config = os.path.join(temporary_directory, 'test.yml')
    with open(config, 'w') as cfg:
        cfg.write(textwrap.dedent("""\
            applications:
                - path: /foo/*
                  application: onegov.core.framework.Framework
                  namespace: foo
                  configuration:
                    dsn: {}
                    identity_secure: False
                    identity_secret: asdf
                    csrf_secret: asdfasdf
                    filestorage: fs.osfs.OSFS
                    filestorage_options:
                      root_path: '{}/file-storage'
                      create: true
        """.format(postgres_dsn, temporary_directory)))

    session_manager.ensure_schema_exists("foo-bar")
    session_manager.ensure_schema_exists("foo-fah")

    with patch('onegov.core.upgrade.get_upgrade_modules') as get_modules_1:
        with patch('onegov.core.cli.get_upgrade_modules') as get_modules_2:

            class Upgrades:
                @staticmethod
                @upgrade_task(name='Foobar')
                def run_upgrade(context):
                    pass

            get_modules_1.return_value = get_modules_2.return_value = [
                ('onegov.test', Upgrades)
            ]

            # first run, no tasks are executed because the db is empty
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--config', config,
                '--namespace', 'foo',
                'upgrade'
            ], catch_exceptions=False)

            output = result.output.split('\n')
            assert 'Running upgrade for foo/bar' in output[0]
            assert 'no pending upgrade tasks found' in output[1]
            assert 'Running upgrade for foo/fah' in output[2]
            assert 'no pending upgrade tasks found' in output[3]
            assert result.exit_code == 0

            class NewUpgrades:
                @staticmethod
                @upgrade_task(name='Barfoo')
                def run_upgrade(context):
                    pass

            get_modules_1.return_value = get_modules_2.return_value = [
                ('onegov.test', NewUpgrades)
            ]

            # second run with a new task which will be executed
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--config', config,
                '--namespace', 'foo',
                'upgrade',
                '--dry-run'
            ], catch_exceptions=False)

            output = result.output.split('\n')
            assert 'Running upgrade for foo/bar' in output[0]
            assert 'Barfoo' in output[1]
            assert 'executed 1 upgrade tasks' in output[2]
            assert 'Running upgrade for foo/fah' in output[3]
            assert 'Barfoo' in output[4]
            assert 'executed 1 upgrade tasks' in output[5]
            assert result.exit_code == 0

            # we used dry-run above, so running it again yields the same result
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--config', config,
                '--namespace', 'foo',
                'upgrade',
            ], catch_exceptions=False)

            output = result.output.split('\n')
            assert 'Running upgrade for foo/bar' in output[0]
            assert 'Barfoo' in output[1]
            assert 'executed 1 upgrade tasks' in output[2]
            assert 'Running upgrade for foo/fah' in output[3]
            assert 'Barfoo' in output[4]
            assert 'executed 1 upgrade tasks' in output[5]
            assert result.exit_code == 0

            # the task has now been completed and it won't be executed again
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--config', config,
                '--namespace', 'foo',
                'upgrade',
            ], catch_exceptions=False)

            output = result.output.split('\n')
            assert 'Running upgrade for foo/bar' in output[0]
            assert 'no pending upgrade tasks found' in output[1]
            assert 'Running upgrade for foo/fah' in output[2]
            assert 'no pending upgrade tasks found' in output[3]
            assert result.exit_code == 0
