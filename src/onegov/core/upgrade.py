from __future__ import annotations

import inspect
import importlib
import pkg_resources
import transaction

from contextlib import contextmanager
from inspect import getmembers, isfunction, ismethod
from itertools import chain
from onegov.core import LEVELS
from onegov.core.orm import Base, find_models
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from sqlalchemy import Column, Text, text, bindparam
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import load_only
from sqlalchemy.pool import StaticPool
from toposort import toposort


from typing import cast, overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import (
        Callable, Collection, Iterable, Iterator, Mapping, Sequence)
    # FIXME: Switch to importlib.resources
    from pkg_resources import Distribution, EntryPoint
    from sqlalchemy.engine import Connection
    from sqlalchemy.orm import Query, Session
    from types import CodeType, ModuleType
    from typing import ParamSpec, Protocol, TypeAlias, TypeGuard

    from .request import CoreRequest

    _T = TypeVar('_T')
    _T_co = TypeVar('_T_co', covariant=True)
    _P = ParamSpec('_P')

    class _Task(Protocol[_P, _T_co]):
        __name__: str
        __code__: CodeType
        task_name: str
        always_run: bool
        requires: str | None
        raw: bool

        def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T_co: ...

    RawFunc: TypeAlias = Callable[[Connection, Sequence[str]], Any]
    UpgradeFunc: TypeAlias = Callable[['UpgradeContext'], Any]
    RawTask: TypeAlias = _Task[[Connection, Sequence[str]], Any]
    UpgradeTask: TypeAlias = _Task[['UpgradeContext'], Any]
    TaskCallback: TypeAlias = Callable[[_Task[..., Any]], Any]


class UpgradeState(Base, TimestampMixin):
    """ Keeps the state of all upgrade steps over all modules. """

    __tablename__ = 'upgrades'

    # the name of the module (e.g. onegov.core)
    module = Column(Text, primary_key=True)

    # a json holding the state of the upgrades
    state = Column(JSON, nullable=False, default=dict)

    @property
    def executed_tasks(self) -> set[str]:
        if not self.state:
            return set()
        else:
            return set(self.state.get('executed_tasks', []))

    def was_already_executed(self, task: _Task[..., Any]) -> bool:
        return task.task_name in self.executed_tasks

    def mark_as_executed(self, task: _Task[..., Any]) -> None:
        if not self.state:
            self.state = {}

        if 'executed_tasks' in self.state:
            self.state['executed_tasks'].append(task.task_name)
            self.state['executed_tasks'] = list(
                set(self.state['executed_tasks']))
        else:
            self.state['executed_tasks'] = [task.task_name]

        self.state.changed()  # type:ignore[attr-defined]


def get_distributions_with_entry_map(
    key: str
) -> Iterator[tuple[Distribution, dict[str, EntryPoint]]]:
    """ Iterates through all distributions with entry_maps and yields
    each distribution along side the entry map with the given key.

    """
    for distribution in pkg_resources.working_set:
        if hasattr(distribution, 'get_entry_map'):
            entry_map = distribution.get_entry_map(key)

            if entry_map:
                yield distribution, entry_map


def get_upgrade_modules() -> Iterator[tuple[str, ModuleType]]:
    """ Returns all modules that registered themselves for onegov.core
    upgrades like this::

        entry_points={
            'onegov': [
                'upgrade = onegov.mypackage.upgrade'
            ]
        }

    To add multiple upgrades in a single setup.py file, the following syntax
    may be used. This will become the default in the future::

        entry_points= {
            'onegov_upgrades': [
                'onegov.mypackage = onegov.mypackage.upgrade'
            ]
        }

    Note that the part before the ``=``-sign should be kept the same, even if
    the location changes. Otherwise completed updates may be run again!

    """
    yield 'onegov.core', importlib.import_module('onegov.core.upgrades')

    distributions = get_distributions_with_entry_map('onegov')

    for distribution, entry_map in distributions:
        if 'upgrade' in entry_map:
            yield (
                '.'.join(entry_map['upgrade'].module_name.split('.')[:2]),
                importlib.import_module(entry_map['upgrade'].module_name)
            )

    distributions = get_distributions_with_entry_map('onegov_upgrades')

    for distribution, entry_map in distributions:
        for entry in entry_map.values():
            yield entry.name, importlib.import_module(entry.module_name)


class upgrade_task:  # noqa: N801
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

    def __init__(
        self,
        name: str,
        always_run: bool = False,
        requires: str | None = None,
        raw: bool = False
    ):
        if raw:
            assert always_run, 'raw tasks must always run'
            assert not requires, 'raw tasks may not require other tasks'

        self.name = name
        self.always_run = always_run
        self.requires = requires
        self.raw = raw

    # NOTE: We only allow the two supported function signatures
    @overload
    def __call__(self, fn: UpgradeFunc) -> UpgradeTask: ...
    @overload
    def __call__(self, fn: RawFunc) -> RawTask: ...

    def __call__(self, fn: Callable[_P, _T]) -> _Task[_P, _T]:
        fn = cast('_Task[_P, _T]', fn)
        fn.task_name = self.name
        fn.always_run = self.always_run
        fn.requires = self.requires
        fn.raw = self.raw
        return fn


def is_task(function: Callable[_P, _T]) -> TypeGuard[_Task[_P, _T]]:
    """ Returns True if the given function is an uprade task. """
    if not (isfunction(function) or ismethod(function)):
        return False

    return hasattr(function, 'task_name')


def get_module_tasks(module: ModuleType) -> Iterator[_Task[..., Any]]:
    """ Goes through a module or class and returns all upgrade tasks. """
    for name, function in getmembers(module, is_task):
        yield function


def get_tasks_by_id(
    upgrade_modules: Iterable[tuple[str, ModuleType]]
) -> dict[str, _Task[..., Any]]:
    """ Takes a list of upgrade modules or classes and returns the tasks
    keyed by id.

    """

    tasks = {}
    fn_names = set()

    for distribution, upgrade_module in upgrade_modules:

        for function in get_module_tasks(upgrade_module):
            task_id = f'{distribution}:{function.task_name}'

            assert task_id not in tasks, 'Duplicate task'
            tasks[task_id] = function

            # make sure we don't have duplicate function names - it works, but
            # it makes debugging harder
            msg = f'Duplicate function name: {function.__name__}'
            assert function.__name__ not in fn_names, msg

            fn_names.add(function.__name__)

    return tasks


def get_module_order_key(
    tasks: Mapping[str, _Task[..., Any]]
) -> Callable[[str], SupportsRichComparison]:
    """ Returns a sort order key which orders task_ids in order of their
    module dependencies. That is a task from onegov.core is sorted before
    a task in onegov.user, because onegov.user depends on onegov.core.

    This is used to order unrelated tasks in a sane way.

    """
    sorted_modules = {module: ix for ix, module in enumerate(chain(*LEVELS))}

    def sortkey(task: str) -> SupportsRichComparison:
        module = task.split(':', 1)[0]
        return (
            # sort by level (unknown models first)
            sorted_modules.get(module, float('-inf')),

            # then by module name
            module,

            # then by appearance of update function in the code
            tasks[task].__code__.co_firstlineno
        )

    return sortkey


def get_tasks(
    upgrade_modules: Iterable[tuple[str, ModuleType]] | None = None
) -> list[tuple[str, _Task[..., Any]]]:
    """ Takes a list of upgrade modules or classes and returns the
    tasks that should be run in the order they should be run.

    The order takes dependencies into account.

    """

    tasks = get_tasks_by_id(upgrade_modules or get_upgrade_modules())

    for task_id, task in tasks.items():
        if task.requires:
            assert task.requires in tasks, f'Could not find "{task.requires}"'
            assert not tasks[task.requires].raw, 'Raw tasks cannot be required'

    graph: dict[str, set[str]] = {}

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


def register_modules(
    session: Session,
    modules: Iterable[tuple[str, ModuleType]],
    tasks: Collection[tuple[str, _Task[..., Any]]]
) -> None:
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


def register_all_modules_and_tasks(session: Session) -> None:
    """ Registers all the modules and all the tasks. """
    register_modules(session, get_upgrade_modules(), get_tasks())


class UpgradeTransaction:
    """ Holds the session and the alembic operations connection together and
    commits/aborts both at the same time.

    Not really a two-phase commit solution. That could be accomplished but
    for now this suffices.

    """

    def __init__(self, context: UpgradeContext):
        conn = context.operations_connection
        tx = conn.begin_nested() if conn.in_transaction() else conn.begin()
        self.operations_transaction = tx
        self.session = context.session

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.operations_transaction.commit()
        transaction.commit()

    def abort(self) -> None:
        self.operations_transaction.rollback()
        transaction.abort()


class UpgradeContext:
    """ Holdes the context of the upgrade. An instance of this is passed
    to each upgrade task.

    """

    # FIXME: alembic currently auto generates type stubs for alembic.op but
    #        not for Operations, we should probably make a PR, for Operations
    #        to be auto-generated as well, so we get the available methods
    operations: Any

    def __init__(self, request: CoreRequest):

        # alembic is a somewhat heavy import (thanks to the integrated mako)
        # -> since we really only ever need it during upgrades we lazy load
        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        # we need to reset the request session property every time because
        # we reuse the request over various session managers
        if 'session' in request.__dict__:
            del request.__dict__['session']

        self.request = request
        self.session = session = request.session
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
        conn = session._connection_for_bind(  # type:ignore[attr-defined]
            session.bind)
        self.operations_connection: Connection = conn
        self.operations = Operations(
            MigrationContext.configure(self.operations_connection))

    def begin(self) -> UpgradeTransaction:
        return UpgradeTransaction(self)

    def has_column(self, table: str, column: str) -> bool:
        inspector = Inspector(self.operations_connection)
        return column in {c['name'] for c in inspector.get_columns(
            table, schema=self.schema
        )}

    def has_constraint(
        self, table_name: str, constraint_name: str, constraint_type: str
    ) -> bool:
        """ Check if a specific constraint exists on a table.

        When constraint names aren't known, they can be discovered:

        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_name = 'table_name'
        AND constraint_name LIKE '%column_name%';
        """
        return self.session.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = :schema
                  AND table_name = :table_name
                  AND constraint_type = :constraint_type
                  AND constraint_name = :constraint_name
            )
        """
            ).bindparams(
                bindparam('schema', self.schema),
                bindparam('table_name', table_name),
                bindparam('constraint_name', constraint_name),
                bindparam('constraint_type', constraint_type),
        )
        ).scalar()

    def has_enum(self, enum_name: str) -> bool:
        return self.session.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type
                WHERE typname = :enum_name
                  AND typnamespace = (
                    SELECT oid FROM pg_namespace
                    WHERE nspname = :schema
                  )
            )
        """).bindparams(
            bindparam('schema', self.schema),
            bindparam('enum_name', enum_name)
        )).scalar()

    def has_table(self, table: str) -> bool:
        inspector = Inspector(self.operations_connection)
        return table in inspector.get_table_names(schema=self.schema)

    def get_enum_values(self, enum_name: str) -> set[str]:
        result = self.operations_connection.execute(
            text("""
            SELECT pg_enum.enumlabel AS value
              FROM pg_enum
              JOIN pg_type
                ON pg_type.oid = pg_enum.enumtypid
             WHERE pg_type.typname = :enum_name
             GROUP BY pg_enum.enumlabel
            """),
            {'enum_name': enum_name}
        )
        return {value for (value,) in result}

    def update_enum_values(
        self,
        enum_name: str,
        enum_values: Iterable[str]
    ) -> bool:
        existing = self.get_enum_values(enum_name)
        missing = set(enum_values) - existing
        if not missing:
            return False

        # HACK: ALTER TYPE has to be run outside transaction
        self.operations.execute(text('COMMIT'))
        for value in missing:
            # NOTE: This should be safe just by virtue of naming
            #       restrictions on classes and enum members
            self.operations.execute(text(
                f"ALTER TYPE {enum_name} ADD VALUE '{value}'"
            ))
        # start a new transaction
        self.operations.execute(text('BEGIN'))
        return True

    def models(self, table: str) -> Iterator[Any]:
        def has_matching_tablename(model: Any) -> bool:
            if not hasattr(model, '__tablename__'):
                return False  # abstract bases

            return model.__tablename__ == table

        for base in self.request.app.session_manager.bases:
            yield from find_models(base, has_matching_tablename)

    def records_per_table(
        self,
        table: str,
        columns: Iterable[Column[Any]] | None = None
    ) -> Iterator[Any]:

        if columns is None:
            def filter_columns(q: Query[Any]) -> Query[Any]:
                return q
        else:
            column_names = tuple(c.name for c in columns)

            def filter_columns(q: Query[Any]) -> Query[Any]:
                return q.options(load_only(*column_names))

        for model in self.models(table):
            yield from filter_columns(self.session.query(model))

    @contextmanager
    def stop_search_updates(self) -> Iterator[None]:
        # XXX this would be better handled with a more general approach
        # that doesn't require knowledge of onegov.search
        if hasattr(self.app, 'fts_orm_events'):
            self.app.fts_orm_events.stopped = True
            yield
            self.app.fts_orm_events.stopped = False
        else:
            yield

    def is_empty_table(self, table: str) -> bool:
        return self.operations_connection.execute(text(
            f'SELECT * FROM {table} LIMIT 1')).rowcount == 0

    def add_column_with_defaults(
        self,
        table: str,
        column: Column[_T],
        default: _T | Callable[[Any], _T]
    ) -> None:
        # XXX while adding default values we shouldn't reindex the data
        # since this is what the default add_column code does and will be
        # doing in the future when Postgres 11 supports defaults for
        # new columns - the way this is implemented now is with tight coupling
        # that we shouldn't do, but we want to replace this when Postgres 11
        # comes around
        with self.stop_search_updates():
            nullable_column = column.copy()
            nullable_column.nullable = True

            self.operations.add_column(table, nullable_column)

            if not self.is_empty_table(table):
                # fill it with defaults if the tables has any rows
                for record in self.records_per_table(table, (column, )):
                    value = default(record) if callable(default) else default
                    setattr(record, column.name, value)

                    if hasattr(getattr(record, column.name), 'changed'):
                        getattr(record, column.name).changed()

                # make sure all generated values are flushed
                self.session.flush()

            # activate non-null constraint
            if not column.nullable:
                self.operations.alter_column(
                    table, column.name, nullable=False)

            # propagate to db
            self.session.flush()


class RawUpgradeRunner:
    """ Runs the given raw tasks. """

    def __init__(
        self,
        tasks: Sequence[tuple[str, RawTask]],
        commit: bool = True,
        on_task_success: TaskCallback | None = None,
        on_task_fail: TaskCallback | None = None
    ):
        self.tasks = tasks
        self.commit = commit

        # FIXME: We should just move the arguments around or set
        #        a lambda that does noething as the default, or
        #        do what we do in UpgradeRunner
        assert on_task_success is not None
        assert on_task_fail is not None
        self._on_task_success = on_task_success
        self._on_task_fail = on_task_fail

    def run_upgrade(self, dsn: str, schemas: Sequence[str]) -> int:

        # it's possible for applications to exist without schemas, if the
        # application doesn't use multi-tennants and has not been run yet
        if not schemas:
            return 0

        engine = create_engine(dsn, poolclass=StaticPool, future=True)
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


class UpgradeRunner:
    """ Runs the given basic tasks. """

    states: dict[str, UpgradeState]

    def __init__(
        self,
        modules: Sequence[tuple[str, ModuleType]],
        tasks: Sequence[tuple[str, UpgradeTask]],
        commit: bool = True,
        on_task_success: TaskCallback | None = None,
        on_task_fail: TaskCallback | None = None
    ):
        self.modules = modules
        self.tasks = tasks
        self.commit = commit
        self.states = {}

        self._on_task_success = on_task_success
        self._on_task_fail = on_task_fail

    def on_task_success(self, task: UpgradeTask) -> None:
        if self._on_task_success is not None:
            self._on_task_success(task)

    def on_task_fail(self, task: UpgradeTask) -> None:
        if self._on_task_fail is not None:
            self._on_task_fail(task)

    def get_state(self, context: UpgradeContext, module: str) -> UpgradeState:
        if module not in self.states:
            query = context.session.query(UpgradeState)
            query = query.filter(UpgradeState.module == module)

            # assume that all modules have been ran through register_module
            self.states[module] = query.one()

        return context.session.merge(self.states[module], load=True)

    def register_modules(self, request: CoreRequest) -> None:
        register_modules(request.session, self.modules, self.tasks)

        if self.commit:
            transaction.commit()

    def get_module_from_task_id(self, task_id: str) -> str:
        return task_id.split(':', 1)[0]

    def run_upgrade(self, request: CoreRequest) -> int:
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
