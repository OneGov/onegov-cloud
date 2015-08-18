""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('Rename academic_title to salutation')
def add_handler_id_to_ticket(context):

    context.operations.alter_column(
        'people', 'academic_title', new_column_name='salutation')
