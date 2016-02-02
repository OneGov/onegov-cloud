import importlib
import networkx as nx
import pkg_resources
import transaction

from alembic.migration import MigrationContext
from alembic.operations import Operations
from inspect import getmembers, isfunction, ismethod
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from sqlalchemy import Column, Text
from sqlalchemy.engine.reflection import Inspector


class UpgradeState(Base, TimestampMixin):
    """ Keeps the state of all upgrade steps over all modules. """

    __tablename__ = 'upgrades'

    # the name of the module (e.g. onegov.core)
    module = Column(Text, primary_key=True)

    # a json holding the state of the upgrades
    state = Column(JSON, nullable=False, default=dict)

    @property
    def executed_tasks(self):
        if not self.state:
            return set()
        else:
            return set(self.state.get('executed_tasks', []))

    def was_already_executed(self, task):
        return task.task_name in self.executed_tasks

    def mark_as_executed(self, task):
        if not self.state:
            self.state = {}

        if 'executed_tasks' in self.state:
            self.state['executed_tasks'].append(task.task_name)
            self.state['executed_tasks'] = list(
                set(self.state['executed_tasks']))
        else:
            self.state['executed_tasks'] = [task.task_name]

        self.state.changed()


def get_distributions_with_entry_map(key):
    """ Iterates through all distributions with entry_maps and yields
    each distribution along side the entry map with the given key.

    """
    for distribution in pkg_resources.working_set:
        if hasattr(distribution, 'get_entry_map'):
            entry_map = distribution.get_entry_map(key)

            if entry_map:
                yield distribution, entry_map


def get_upgrade_modules():
    """ Returns all modules that registered themselves for onegov.core
    upgrades like this::

        entry_points={
            'onegov.core': [
                'upgrade = onegov.mypackage.upgrade'
            ]
        }

    """
    for distribution, entry_map in get_distributions_with_entry_map('onegov'):
        if 'upgrade' in entry_map:
            yield (
                '.'.join(entry_map['upgrade'].module_name.split('.')[:2]),
                importlib.import_module(entry_map['upgrade'].module_name)
            )


class upgrade_task(object):
    """ Marks the decorated function as an upgrade task. Upgrade tasks should
    be defined outside classes (except for testing) - that is in the root of
    the module (directly in onegov/form/upgrades.py for example).

    Each upgrade task has the following properties:

    :name:
        The name of the task in readable English. Do not change the name of
        the task once you pushed your changes. This name is used as an id!

    :always_run:
        By default, tasks are run once on if they haven't been run yet, or if
        the module was not yet under upgrade control (it just added itself
        through the entry_points mechanism).

        There are times where this is not wanted.

        If you enable upgrades in your module and you plan to run an upgrade
        task in the same release, then you need to 'always_run' and detect
        yourself if you need to do any changes.

        If you need to enable upgrades and run a task at the same time which
        can only be run once and is impossible to make idempotent, then you
        need to make two releases. One that enables upgade control and a second
        one that

        Also, if you want to run an upgrade task every time you upgrade (for
        example, for maintenance), then you should also use it.

        The easiest way to use upgrade control is to enable it from the first
        release on.

        Another way to tackle this is to write update methods idempotent as
        often as possible and to always run them.

    :requires:
        A reference to another projects upgrade task that should be run first.

        For example::

            requires='onegov.form:Add new form field'

        If the reference cannot be found, the upgrade fails.

    Always run tasks may return ``False`` if they wish to be considered
    as not run (and therefore not shown in the upgrade runner).

    """

    def __init__(self, name, always_run=False, requires=None):
        self.name = name
        self.always_run = always_run
        self.requires = requires

    def __call__(self, fn):
        fn.task_name = self.name
        fn.always_run = self.always_run
        fn.requires = self.requires
        return fn


def is_task(function):
    """ Returns True if the given function is an uprade task. """
    if not (isfunction(function) or ismethod(function)):
        return False

    return hasattr(function, 'task_name')


def get_module_tasks(module):
    """ Goes through a module or class and returns all upgrade tasks. """
    for name, function in getmembers(module, is_task):
        yield function


def get_tasks_by_id(upgrade_modules=None):
    """ Takes a list of upgrade modules or classes and returns the tasks
    keyed by id.

    """

    tasks = {}
    fn_names = set()

    for distribution, upgrade_module in upgrade_modules:

        for function in get_module_tasks(upgrade_module):
            task_id = ':'.join((distribution, function.task_name))

            assert task_id not in tasks, "Duplicate task"
            tasks[task_id] = function

            # make sure we don't have duplicate function names - it works, but
            # it makes debugging harder
            assert function.__name__ not in fn_names, "Duplicate function name"
            fn_names.add(function.__name__)

    return tasks


def get_tasks(upgrade_modules=None):
    """ Takes a list of upgrade modules or classes and returns the
    tasks that should be run in the order they should be run.

    The order takes dependencies into account.

    """

    tasks = get_tasks_by_id(upgrade_modules or get_upgrade_modules())
    ordered_tasks = []
    roots = set()
    graph = nx.DiGraph()

    for task_id, task in tasks.items():
        if task.requires is None:
            roots.add(task_id)
        else:
            graph.add_edge(task.requires, task_id)

    for task_id in sorted(roots):
        ordered_tasks.append((task_id, tasks[task_id]))

        try:
            for _, task_id in nx.dfs_edges(graph, task_id):
                ordered_tasks.append((task_id, tasks[task_id]))
        except KeyError:
            pass

    return ordered_tasks


def register_modules(session, modules, tasks):
    """ Sets up the state tracking for all modules. Initially, all tasks
    are marekd as executed, because we assume tasks to upgrade older
    deployments to a new deployment.

    If this is a new deployment we do not need to execute these tasks.

    Tasks where this is not desired should be marked as 'always_run'.
    They will then manage their own state (i.e. check if they need to
    run or not).

    This function is idempotent.

    """

    for module, upgrade_module in modules:
        query = session.query(UpgradeState)
        query = query.filter(UpgradeState.module == module)

        if query.first():
            continue

        session.add(
            UpgradeState(module=module, state={
                'executed_tasks': [
                    task.task_name for task_id, task in tasks
                    if task_id.startswith(module)
                ]
            })
        )

    session.flush()


def register_all_modules_and_tasks(session):
    """ Registers all the modules and all the tasks. """
    register_modules(session, get_upgrade_modules(), get_tasks())


class UpgradeTransaction(object):
    """ Holds the session and the alembic operations connection together and
    commits/aborts both at the same time.

    Not really a two-phase commit solution. That could be accomplished but
    for now this suffices.

    """

    def __init__(self, context):
        self.operations_transaction = context.operations_connection.begin()
        self.session = context.session

    def flush(self):
        self.session.flush()

    def commit(self):
        self.operations_transaction.commit()
        transaction.commit()

    def abort(self):
        self.operations_transaction.rollback()
        transaction.abort()


class UpgradeContext(object):
    """ Holdes the context of the upgrade. An instance of this is passed
    to each upgrade task.

    """

    def __init__(self, request):
        self.request = request
        self.session = request.app.session()
        self.app = request.app
        self.schema = request.app.session_manager.current_schema
        self.engine = self.session.bind

        # The locale of the upgrade is the default locale
        request.app.session_manager.set_locale(
            current_locale=self.request.locale,
            default_locale=self.request.default_locale
        )

        # Make sure the connection is the same for the session, the engine
        # and the alembic migrations context. Otherwise the upgrade locks up.
        # If that happens again, test with this:
        #
        #       http://docs.sqlalchemy.org/en/latest/core/pooling.html
        #       #sqlalchemy.pool.AssertionPool
        #
        self.operations_connection = self.session._connection_for_bind(
            self.session.bind)
        self.operations = Operations(
            MigrationContext.configure(self.operations_connection))

    def begin(self):
        return UpgradeTransaction(self)

    def has_column(self, table, column):
        inspector = Inspector(self.operations_connection)
        return column in {c['name'] for c in inspector.get_columns(table)}


class UpgradeRunner(object):
    """ Runs all tasks of a :class:`UpgradeTasksRegistry`. """

    def __init__(self, modules, tasks, commit=True,
                 on_task_success=None, on_task_fail=None):
        self.modules = modules
        self.tasks = tasks
        self.commit = commit
        self.states = {}

        self._on_task_success = on_task_success
        self._on_task_fail = on_task_fail

    def on_task_success(self, task):
        if self._on_task_success is not None:
            self._on_task_success(task)

    def on_task_fail(self, task):
        if self._on_task_fail is not None:
            self._on_task_fail(task)

    def get_state(self, context, module):
        if module not in self.states:
            query = context.session.query(UpgradeState)
            query = query.filter(UpgradeState.module == module)

            # assume that all modules have been ran through register_module
            self.states[module] = query.one()

        return context.session.merge(self.states[module], load=False)

    def register_modules(self, request):
        register_modules(request.app.session(), self.modules, self.tasks)

        if self.commit:
            transaction.commit()

    def get_module_from_task_id(self, task_id):
        return task_id.split(':')[0]

    def run_upgrade(self, request):
        self.register_modules(request)

        tasks = ((self.get_module_from_task_id(i), t) for i, t in self.tasks)
        executed = 0

        for module, task in tasks:
            context = UpgradeContext(request)
            state = self.get_state(context, module)

            if not task.always_run and state.was_already_executed(task):
                continue

            upgrade = context.begin()

            try:
                result = task(context)

                # mark all tasks as executed, even 'always run' ones
                state.mark_as_executed(task)
                upgrade.flush()

                # always-run tasks which return False are considered
                # to have not run
                hidden = task.always_run and result is False

                if not hidden:
                    executed += 1
                    self.on_task_success(task)

            except:
                upgrade.abort()
                self.on_task_fail(task)

                raise
            else:
                if self.commit:
                    upgrade.commit()
                else:
                    upgrade.abort()
            finally:
                context.session.invalidate()
                context.engine.dispose()

        return executed
