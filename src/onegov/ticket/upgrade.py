""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from decimal import Decimal
from onegov.core.orm.types import JSON, UTCDateTime, UUID
from onegov.core.upgrade import upgrade_task
from onegov.pay import PaymentProvider
from onegov.ticket import Ticket, TicketInvoice
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy import column, text, update, func, and_, true, false, Numeric
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy.dialects.postgresql import ARRAY, HSTORE
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add handler_id to ticket')
def add_handler_id_to_ticket(context: UpgradeContext) -> None:

    if not context.has_column('tickets', 'handler_id'):
        context.operations.add_column(
            'tickets', Column(
                'handler_id', Text, nullable=True, unique=True, index=True
            )
        )

        for ticket in context.session.query(Ticket).all():
            # this should probably use [] access, but either way it will
            # fail in the alter column below if some handler_ids ended
            # up being NULL at the end, so let's just ignore it
            ticket.handler_id = ticket.handler_data.get(  # type:ignore
                'submission_id'
            )
            ticket.handler_data = {}

        context.session.flush()

        context.operations.alter_column(
            'tickets', 'handler_id', nullable=False
        )


@upgrade_task('Add snapshot json column to ticket')
def add_snapshot_json_column_to_ticket(context: UpgradeContext) -> None:

    context.operations.add_column(
        'tickets', Column('snapshot', JSON, nullable=True)
    )

    for ticket in context.session.query(Ticket).all():
        ticket.snapshot = {}

    context.session.flush()
    context.operations.alter_column('tickets', 'snapshot', nullable=False)


@upgrade_task('Add subtitle to ticket')
def add_subtitle_to_ticket(context: UpgradeContext) -> None:

    context.operations.add_column(
        'tickets', Column('subtitle', Text, nullable=True))

    for ticket in context.session.query(Ticket).all():
        ticket.subtitle = ticket.handler.subtitle

    context.session.flush()


@upgrade_task('Add process time to ticket')
def add_process_time_to_ticket(context: UpgradeContext) -> None:

    if not context.has_column('tickets', 'last_state_change'):
        context.operations.add_column(
            'tickets', Column('last_state_change', UTCDateTime, nullable=True))

    if not context.has_column('tickets', 'reaction_time'):
        context.operations.add_column(
            'tickets', Column('reaction_time', Integer, nullable=True))

    if not context.has_column('tickets', 'process_time'):
        context.operations.add_column(
            'tickets', Column('process_time', Integer, nullable=True))


@upgrade_task('Add muted state to ticket')
def add_muted_state_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'muted'):
        return

    context.operations.add_column(
        'tickets', Column('muted', Boolean, nullable=True))

    for ticket in context.session.query(Ticket):
        ticket.muted = False

    context.session.flush()
    context.operations.alter_column('tickets', 'muted', nullable=False)


@upgrade_task('Add archived flag to ticket')
def add_archived_flag_to_ticket(context: UpgradeContext) -> None:
    pass


@upgrade_task('Add archived as a state and remove flag')
def add_archived_state_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'archived'):
        context.operations.drop_column('tickets', 'archived')

    old_type = Enum(
        'open',
        'pending',
        'closed',
        name='ticket_state'
    )
    new_type = Enum(
        'open',
        'pending',
        'closed',
        'archived',
        name='ticket_state'
    )
    tmp_type = Enum(
        'open',
        'pending',
        'closed',
        'archived',
        name='ticket_state_'
    )
    op = context.operations
    tmp_type.create(op.get_bind(), checkfirst=False)

    op.execute(text("""
        ALTER  TABLE tickets ALTER COLUMN state TYPE ticket_state_
        USING state::text::ticket_state_;
    """))

    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(context.operations.get_bind(), checkfirst=False)

    op.execute(text("""
        ALTER TABLE tickets ALTER COLUMN state TYPE ticket_state
        USING state::text::ticket_state
    """))
    tmp_type.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Add closed on column to ticket 3')
def add_closed_on_column_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'closed_on'):
        return

    context.operations.add_column(
        'tickets', Column('closed_on', UTCDateTime, nullable=True)
    )

    stmt = update(Ticket.__table__).where(
        and_(
            Ticket.__table__.c.state.in_(('closed', 'archived')),
            Ticket.__table__.c.reaction_time.isnot(None),
            Ticket.__table__.c.process_time.isnot(None)
        )
    ).values(
        closed_on=Ticket.__table__.c.created +
                  func.make_interval(secs=Ticket.__table__.c.reaction_time) +
                  func.make_interval(secs=Ticket.__table__.c.process_time)
    )
    context.session.execute(stmt)
    context.session.flush()


@upgrade_task('Add exclusive/notification columns to ticket permission')
def add_exclusive_and_notification_columns_to_ticket_permission(
    context: UpgradeContext
) -> None:

    context.operations.add_column(
        'ticket_permissions',
        Column(
            'exclusive',
            Boolean,
            nullable=False,
            server_default=true(),
            index=True,
        )
    )

    context.operations.add_column(
        'ticket_permissions',
        Column(
            'immediate_notification',
            Boolean,
            nullable=False,
            server_default=false(),
            index=True,
        )
    )

    if not context.has_constraint(
        'ticket_permissions',
        'no_redundant_ticket_permissions',
        'CHECK'
    ):
        context.operations.create_check_constraint(
            'no_redundant_ticket_permissions',
            'ticket_permissions',
            column('exclusive').isnot_distinct_from(True)
            | column('immediate_notification').isnot_distinct_from(True),
        )


@upgrade_task('Add tags and tags_meta columns and index to ticket')
def add_tags_columns_and_index_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'tags'):
        return

    context.operations.add_column(
        'tickets', Column('tags', HSTORE, nullable=True)
    )

    context.operations.add_column(
        'tickets', Column('tags_meta', JSON, nullable=True)
    )

    context.operations.create_index(
        'ix_tickets_tags',
        'tickets',
        ['tags'],
        postgresql_using='gin',
    )


@upgrade_task('Add ticket_email column and index to ticket')
def add_ticket_email_column_and_index(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'ticket_email'):
        return

    context.operations.add_column(
        'tickets', Column('ticket_email', Text, nullable=True)
    )

    context.operations.create_index(
        'ix_ticket_email', 'tickets', ['ticket_email']
    )

    # Fast upgrade path for tickets with snapshots
    context.operations.execute(text("""
        UPDATE tickets
           SET ticket_email = snapshot->>'email'
         WHERE snapshot->'email' IS NOT NULL
    """))

    # Slow upgrade path for open/pending tickets, we won't
    # bother with closed/archived tickets without a snapshot
    for ticket in (
        context.session.query(Ticket)
        # Use load_only to prevent 'UndefinedColumn column tickets.closed_on
        # does not exist' under certain conditions
        .options(load_only(
            Ticket.id,  # Primary key, always loaded but good to be explicit
            Ticket.handler_code,  # For ticket.handler
            Ticket.handler_id,  # For ticket.handler
            Ticket.snapshot,  # Potentially used by handler.email
            Ticket.state,  # Used in filter
            Ticket.ticket_email  # Used in filter and for assignment
        ))
        .filter(Ticket.ticket_email.is_(None))
        .filter(Ticket.state.in_(['open', 'pending']))
    ):
        if (email := ticket.handler.email) is not None:
            ticket.ticket_email = email


@upgrade_task('Add redundant payment_id to ticket')
def add_payment_id_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'payment_id'):
        return

    context.operations.add_column(
        'tickets', Column('payment_id', UUID, nullable=True)
    )

    context.operations.create_index(
        'ix_ticket_payment_id', 'tickets', ['payment_id']
    )

    # There is no fast path for this, since payment_id is not stored
    # in the snapshot.

    # Slow upgrade path for all tickets that might have a payment.
    for ticket in (
        context.session.query(Ticket)
        .options(load_only(
            Ticket.id,
            Ticket.handler_code,
            Ticket.handler_id,
            Ticket.handler_data,
        ))
    ):
        if (payment := ticket.handler.payment) is not None:
            stmt = update(Ticket.__table__).where(
                Ticket.__table__.c.id == ticket.id
            ).values(
                payment_id=payment.id
            )
            context.session.execute(stmt)

    context.session.flush()


@upgrade_task('Add missing foreign key constraint')
def add_foreign_key_constraint_to_payment_id(context: UpgradeContext) -> None:
    if not context.has_constraint(
        'tickets', 'fk_payments_tickets', 'FOREIGN KEY'
    ):
        context.operations.create_foreign_key(
            'fk_payments_tickets',
            'tickets',
            'payments',
            ['payment_id'],
            ['id']
        )


@upgrade_task(
    'Add new invoice columns',
    requires='onegov.activity:Update invoice tables for polymorphism'
)
def add_new_invoice_columns(context: UpgradeContext) -> None:
    if not context.has_column('tickets', 'invoice_id'):
        context.operations.add_column(
            'tickets', Column(
                'invoice_id',
                UUID,
                ForeignKey('invoices.id'),
                nullable=True
            )
        )
        context.operations.create_index(
            'ix_tickets_invoice_id',
            'tickets',
            ['invoice_id']
        )
    if not context.has_column('invoice_items', 'submission_id'):
        context.operations.add_column(
            'invoice_items', Column(
                'submission_id',
                UUID,
                ForeignKey('submissions.id'),
                nullable=True
            )
        )
        context.operations.create_index(
            'ix_invoices_submission_id',
            'invoice_items',
            ['submission_id']
        )
    if not context.has_column('invoice_items', 'reservation_id'):
        context.operations.add_column(
            'invoice_items', Column(
                'reservation_id',
                Integer,
                nullable=True
            )
        )
        context.operations.create_index(
            'ix_invoices_reservation_id',
            'invoice_items',
            ['reservation_id']
        )
    if not context.has_column('invoice_items', 'vat_factor'):
        context.operations.add_column(
            'invoice_items', Column(
                'vat_factor',
                Numeric(precision=5, scale=4),
                nullable=True
            )
        )

    # NOTE: This isn't super reliable, since the settings on the payment
    #       provider could've changed, so there's old payments with different
    #       settings. But it's the best we can do, since we don't store
    #       on the payment, whether or not the fee was charged to the customer
    #       On  the invoice we always want the price without the fee, since
    #       we add it back on top later.
    sources_that_charge_fee_to_customer = {
        source
        for source, in context.session.query(
            PaymentProvider.type
        ).filter(
            PaymentProvider.default.is_(True),
            PaymentProvider.meta['charge_fee_to_customer'] == True
        )
    }

    # generate invoices with a manual item from payments
    # NOTE: For performance reasons we don't try to generate the
    #       individual items. They can later be generated on-demand
    #       when a reservation/form submission is altered and this
    #       manual item can then be deleted afterwards.
    for ticket in (
        context.session.query(Ticket)
        .options(
            load_only(
                Ticket.id,
                Ticket.title,
                Ticket.payment_id,
            )
        )
        .filter(Ticket.payment_id.isnot(None))
        .options(selectinload(Ticket.payment))
    ):
        payment = ticket.payment
        assert payment is not None
        invoice = TicketInvoice(
            id=uuid4(),
            ticket=ticket,
        )
        context.session.add(invoice)
        if payment.source in sources_that_charge_fee_to_customer:
            amount = payment.net_amount
        else:
            amount = payment.amount
        item = invoice.add(
            text=ticket.title,
            group='migration',
            unit=amount,
            quantity=Decimal('1'),
            paid=payment.state == 'paid',
            flush=False
        )
        item.payments.append(payment)
        item.paid = payment.state == 'paid'

    context.session.flush()


@upgrade_task('Add order_id to ticket')
def add_order_id_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'order_id'):
        return

    context.operations.add_column(
        'tickets', Column('order_id', UUID, nullable=True)
    )

    context.operations.create_index(
        'ix_tickets_order_id', 'tickets', ['order_id']
    )


@upgrade_task('Add customer_message_ids to ticket')
def add_customer_message_ids_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'customer_message_ids'):
        return

    context.operations.add_column(
        'tickets', Column('customer_message_ids', ARRAY(String), nullable=True)
    )
