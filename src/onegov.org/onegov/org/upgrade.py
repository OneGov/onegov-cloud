""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('Move from town to organisation')
def move_town_to_organisation(context):
    context.operations.drop_table('organisations')
    context.operations.rename_table('towns', 'organisations')
