""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('Remove department column')
def remove_department_column(context):
    if context.has_column('fsi_attendees', 'department'):
        context.operations.drop_column('fsi_attendees', 'department')
