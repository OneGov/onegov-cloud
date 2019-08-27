""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Text


@upgrade_task('Add remote_id field to payments')
def add_remote_id_field_to_payments(context):
    if not context.has_column('payments', 'remote_id'):
        context.operations.add_column('payments', Column(
            'remote_id', Text, nullable=True
        ))
