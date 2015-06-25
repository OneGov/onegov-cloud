import importlib
import pkg_resources

from inspect import getmembers, isfunction


def get_upgrade_modules():
    for distribution in pkg_resources.working_set:

        if hasattr(distribution, 'get_entry_map'):
            entry_points = distribution.get_entry_map('onegov')
        else:
            entry_points = None

        if entry_points and 'upgrade' in entry_points:
            yield (
                distribution.name,
                importlib.import_module(entry_points['upgrade'])
            )


def get_upgrade_tasks(module):
    for name, function in getmembers(module, isfunction):
        if hasattr(function, 'task_name'):
            yield function


class UpgradeRunner(object):

    def __init__(self, upgrade_modules=None):

        upgrade_modules = upgrade_modules or get_upgrade_modules()

        upgrade_task_ids = set()
        upgrade_tasks = []

        for distribution, upgrade_module in upgrade_modules:
            for function in get_upgrade_tasks(upgrade_module):
                task_id = ':'.join((distribution, function.task_name))

                assert task_id not in upgrade_task_ids, "Duplicate task"
                upgrade_task_ids.add(task_id)

                function.task_id = task_id
                upgrade_tasks.append(function)

        self.upgrade_tasks = sorted(
            upgrade_tasks, key=lambda f: f.task_name)

    def run_upgrade(self, request):
        for task in self.upgrade_tasks:
            task(request)


class upgrade_task(object):

    def __init__(self, name, always_run=False, requires=None):
        self.name = name
        self.always_run = always_run
        self.requires = requires

    def __call__(self, fn):
        fn.task_name = self.name
        fn.always_run = self.always_run
        fn.requires = self.requires
        return fn
