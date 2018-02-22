import inspect
import importlib
import pkg_resources
import transaction

from alembic.migration import MigrationContext
from alembic.operations import Operations
from inspect import getmembers, isfunction, ismethod
from onegov.core.orm import Base, find_models
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from sqlalchemy import Column, Text
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.pool import StaticPool
from toposort import toposort, toposort_flatten


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
    yield 'onegov.core', importlib.import_module('onegov.core.upgrades')

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

    :raw:
        A raw task is run without setting up a request. Instead a database
        connection and a list of targeted schemas is passed. It's up to the
        upgrade function to make sure the right schemas are targeted through
        that connection!

        This is useful for upgrades which need to execute some raw SQL that
        cannot be executed in a request context. For example, this is a way
        to migrate the upgrade states table of the upgrade itself.

        Raw tasks are always run and there state is not recorded. So the
        raw task needs to be idempotent and return False if there was no
        change.

        Only use this if you have no other way. This is a very blunt instrument
        only used under special circumstances.

        Note, raw tasks may be normal function OR generators. If they are
        generators, then with each yield the transaction is either commited
        or rolled-back depending on the dry-run cli argument.

    Always run tasks may return ``False`` if they wish to be considered
    as not run (and therefore not shown in the upgrade runner).

    """

    def __init__(self, name, always_run=False, requires=None, raw=False):
        if raw:
            assert always_run, "raw tasks must always run"
            assert not requires, "raw tasks may not require other tasks"

        self.name = name
        self.always_run = always_run
        self.requires = requires
        self.raw = raw

    def __call__(self, fn):
        fn.task_name = self.name
        fn.always_run = self.always_run
        fn.requires = self.requires
        fn.raw = self.raw
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


def get_module_order_key(tasks):
    """ Returns a sort order key which orders task_ids in order of their
    module dependencies. That is a task from onegov.core is sorted before
    a task in onegov.user, because onegov.user depends on onegov.core.

    This is used to order unrelated tasks in a sane way.

    """
    modules = set()

    for task in tasks:
        modules.add(task.split(':')[0])

    graph = {}
    packages = pkg_resources.working_set

    for module in modules:
        if module not in graph:
            graph[module] = set()

        if module in packages.by_key:
            for dependency in packages.by_key[module].requires():
                graph[module].add(dependency.key)

    sorted_modules = {
        task_id: ix for ix, task_id in enumerate(toposort_flatten(graph))
    }

    def sortkey(task_id):
        module, name = task_id.split(':', 1)
        return sorted_modules.get(module, float('inf')), task_id

    return sortkey


def get_tasks(upgrade_modules=None):
    """ Takes a list of upgrade modules or classes and returns the
    tasks that should be run in the order they should be run.

    The order takes dependencies into account.

    """

    tasks = get_tasks_by_id(upgrade_modules or get_upgrade_modules())

    for task_id, task in tasks.items():
        if task.requires:
            assert not tasks[task.requires].raw, "Raw tasks cannot be required"

    graph = {}

    for task_id, task in tasks.items():
        if task_id not in graph:
            graph[task_id] = set()

        if task.requires is not None:
            graph[task_id].add(task.requires)

    sorted_tasks = []
    order_key = get_module_order_key(tasks)

    for task_ids in toposort(graph):
        sorted_tasks.extend(sorted(task_ids, key=order_key))

    return [(task_id, tasks[task_id]) for task_id in sorted_tasks]


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

        # we need to reset the request session property every time because
        # we reuse the request over various session managers
        if 'session' in request.__dict__:
            del request.__dict__['session']

        self.request = request
        self.session = request.session
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
        return column in {c['name'] for c in inspector.get_columns(
            table, schema=self.schema
        )}

    def has_table(self, table):
        inspector = Inspector(self.operations_connection)
        return table in inspector.get_table_names(schema=self.schema)

    def models(self, table):
        def has_matching_tablename(model):
            if not hasattr(model, '__tablename__'):
                return False  # abstract bases

            return model.__tablename__ == table

        for base in self.request.app.session_manager.bases:
            yield from find_models(base, has_matching_tablename)

    def records_per_table(self, table):
        for model in self.models(table):
            yield from self.session.query(model)

    def add_column_with_defaults(self, table, column, default):
        # add a nullable column
        nullable_column = column.copy()
        nullable_column.nullable = True

        self.operations.add_column(table, nullable_column)

        # fill it with defaults
        for record in self.records_per_table(table):
            value = default(record) if callable(default) else default
            setattr(record, column.name, value)

            if hasattr(getattr(record, column.name), 'changed'):
                getattr(record, column.name).changed()

        # make sure all generated values are flushed
        self.session.flush()

        # activate non-null constraint
        if not column.nullable:
            self.operations.alter_column(table, column.name, nullable=False)

        # propagate to db
        self.session.flush()


class RawUpgradeRunner(object):
    """ Runs the given raw tasks. """

    def __init__(self, tasks, commit=True,
                 on_task_success=None, on_task_fail=None):
        self.tasks = tasks
        self.commit = commit

        self._on_task_success = on_task_success
        self._on_task_fail = on_task_fail

    def run_upgrade(self, dsn, schemas):

        # it's possible for applications to exist without schemas, if the
        # application doesn't use multi-tennants and has not been run yet
        if not schemas:
            return 0

        engine = create_engine(dsn, poolclass=StaticPool)
        connection = engine.connect()
        executions = 0

        for id, task in self.tasks:
            t = connection.begin()

            try:
                success = False

                if inspect.isgeneratorfunction(task):
                    for changed in task(connection, schemas):
                        success = success or changed

                        if self.commit:
                            t.commit()
                        else:
                            t.rollback()

                        t = connection.begin()
                else:
                    success = task(connection, schemas)

                if success:
                    executions += 1
                    self._on_task_success(task)

            except Exception:
                t.rollback()
                self._on_task_fail(task)

                raise
            else:
                if self.commit:
                    t.commit()
                else:
                    t.rollback()

        return executions


class UpgradeRunner(object):
    """ Runs the given basic tasks. """

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
        register_modules(request.session, self.modules, self.tasks)

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

            except Exception:
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
