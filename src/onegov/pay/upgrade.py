""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add remote_id field to payments')
def add_remote_id_field_to_payments(context: UpgradeContext) -> None:
    if not context.has_column('payments', 'remote_id'):
        context.operations.add_column('payments', Column(
            'remote_id', Text, nullable=True
        ))


@upgrade_task('Make payment models polymorphic type non-nullable')
def make_payment_models_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
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


@upgrade_task('Add enabled to payment providers')
def add_enabled_to_payment_providers(context: UpgradeContext) -> None:
    if not context.has_column('payment_providers', 'enabled'):
        context.add_column_with_defaults(
            table='payment_providers',
            column=Column('enabled', Boolean, nullable=False),
            default=True
        )
