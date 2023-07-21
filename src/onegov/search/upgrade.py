""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task


@upgrade_task('Rename tickets group column')
def rename_tickets_group_column(context):
    if context.has_column('tickets', 'group'):
        context.operations.alter_column(
            table_name='tickets',
            column_name='group',
            new_column_name='group_title'
        )
