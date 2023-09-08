""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import Column


@upgrade_task('Add last modified column')
def add_last_modified_to_assemblies(context):
    if not context.has_column('landsgemeinde_assemblies', 'last_modified'):
        context.operations.add_column(
            'landsgemeinde_assemblies',
            Column('last_modified', UTCDateTime())
        )


@upgrade_task('Remove start time from agenda item and votum')
def remove_start_time_from_agenda_item_and_votum(context):
    for table in ('landsgemeinde_agenda_items', 'landsgemeinde_vota'):
        if context.has_column(table, 'start'):
            context.operations.drop_column(table, 'start')


@upgrade_task('Add last modified column to agenda items')
def add_last_modified_to_agenda_items(context):
    if not context.has_column('landsgemeinde_agenda_items', 'last_modified'):
        context.operations.add_column(
            'landsgemeinde_agenda_items',
            Column('last_modified', UTCDateTime())
        )
