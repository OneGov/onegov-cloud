""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column, Text


@upgrade_task('Add checksum column')
def add_checksum_column(context):
    context.operations.add_column(
        'files', Column('checksum', Text, nullable=True, index=True)
    )
