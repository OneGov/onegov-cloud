""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column, Text


@upgrade_task('Rename yays to yeas', always_run=True)
def rename_yays_to_yeas(context):

    if context.has_column('ballot_results', 'yeas'):
        return False
    else:
        context.operations.alter_column(
            'ballot_results', 'yays', new_column_name='yeas')


@upgrade_task('Add shortcode column')
def add_shortcode_column(context):
    context.operations.add_column('votes', Column('shortcode', Text()))
