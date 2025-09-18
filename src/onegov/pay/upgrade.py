""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations


from onegov.core.upgrade import upgrade_task
from sqlalchemy import false
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


@upgrade_task('Add invoiced state to payments')
def add_invoiced_state_to_payments(context: UpgradeContext) -> None:
    if context.has_table('payments'):
        # On one of the instances this upgrade step failed (ogc-2335)
        # Solution: We end the current transaction first
        # before altering the type

        # End current transaction
        context.operations.execute('COMMIT')

        context.operations.execute(
            "ALTER TYPE payment_state ADD VALUE IF NOT EXISTS 'invoiced'"
        )

        # Start new transaction
        context.operations.execute('BEGIN')


@upgrade_task('Add invoiced column to invoices')
def add_invoiced_state_to_invoices(context: UpgradeContext) -> None:
    if not context.has_table('invoices'):
        return

    if not context.has_column('invoices', 'invoiced'):
        context.operations.add_column(
            'invoices',
            Column(
                'invoiced',
                Boolean,
                nullable=False,
                server_default=false(),
                index=True,
            )
        )

        context.operations.execute("""
            UPDATE invoices
               SET invoiced = TRUE
             WHERE id IN (
                SELECT invoice_items.invoice_id
                  FROM invoice_items
                  JOIN payments_for_invoice_items_payments AS link
                    ON link.invoice_items_id = invoice_items.id
                  JOIN payments
                    ON payments.id = link.payment_id
                 WHERE payments.state = 'invoiced'
            )
        """)
