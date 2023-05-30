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
