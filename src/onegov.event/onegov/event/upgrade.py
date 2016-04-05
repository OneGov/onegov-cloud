""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column


@upgrade_task('Add coordinates column')
def add_coordinates_column(context):
    for table in ('events', 'event_occurrences'):
        context.operations.add_column(
            table, Column('coordinates', JSON(), nullable=True))
