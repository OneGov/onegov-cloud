import importlib
import networkx as nx
import pkg_resources

from inspect import getmembers, isfunction, ismethod


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
                distribution.name,
                importlib.import_module(entry_map['upgrade'])
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
    return isfunction(function) or ismethod(function)\
        and hasattr(function, 'task_name')


def get_module_tasks(module):
    """ Goes through a module or class and returns all upgrade tasks. """
    for name, function in getmembers(module, is_task):
        yield function


def get_tasks_by_id(upgrade_modules=None):
    """ Takes a list of upgrade modules or classes and returns the tasks
    keyed by id.

    """

    tasks = {}

    for distribution, upgrade_module in upgrade_modules:

        for function in get_module_tasks(upgrade_module):
            task_id = ':'.join((distribution, function.task_name))

            assert task_id not in tasks, "Duplicate task"
            tasks[task_id] = function

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


class UpgradeRunner(object):
    """ Runs all tasks of a :class:`UpgradeTasksRegistry`. """

    def __init__(self, tasks):
        self.tasks = tasks

    def run_upgrade(self, request):
        for task_id, task in self.tasks:
            task(request)
