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


@upgrade_task('Make payment models polymorphic type non-nullable')
def make_payment_models_polymorphic_type_non_nullable(context):
    if context.has_table('payments'):
        context.operations.execute("""
            UPDATE payments SET source = 'generic' WHERE source IS NULL;
        """)

        context.operations.alter_column('payments', 'source', nullable=False)

    if context.has_table('payment_providers'):
        context.operations.execute("""
            UPDATE payment_providers SET type = 'generic' WHERE type IS NULL;
        """)

        context.operations.alter_column('payment_providers', 'type',
                                        nullable=False)
