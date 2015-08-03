""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.town import TownApp
from onegov.town.initial_content import add_resources


@upgrade_task('Add initial libres resources', always_run=False)
def add_initial_libres_resources(context):
    if isinstance(context.app, TownApp):
        add_resources(context.app.libres_context)
