""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import JSON, UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.ticket import Ticket
from sqlalchemy import Boolean, Column, Integer, Text, Enum


@upgrade_task('Add handler_id to ticket', always_run=True)
def add_handler_id_to_ticket(context):

    if context.has_column('tickets', 'handler_id'):
        return False
    else:
        context.operations.add_column(
            'tickets', Column(
                'handler_id', Text, nullable=True, unique=True, index=True
            )
        )

        for ticket in context.session.query(Ticket).all():
            ticket.handler_id = ticket.handler_data.get('submission_id')
            ticket.handler_data = {}

        context.session.flush()

        context.operations.alter_column(
            'tickets', 'handler_id', nullable=False
        )


@upgrade_task('Add snapshot json column to ticket')
def add_snapshot_json_column_to_ticket(context):

    context.operations.add_column(
        'tickets', Column('snapshot', JSON, nullable=True)
    )

    for ticket in context.session.query(Ticket).all():
        ticket.snapshot = {}

    context.session.flush()
    context.operations.alter_column('tickets', 'snapshot', nullable=False)


@upgrade_task('Add subtitle to ticket')
def add_subtitle_to_ticket(context):

    context.operations.add_column(
        'tickets', Column('subtitle', Text, nullable=True))

    for ticket in context.session.query(Ticket).all():
        ticket.subtitle = ticket.handler.subtitle

    context.session.flush()


@upgrade_task('Add process time to ticket')
def add_process_time_to_ticket(context):

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
def add_muted_state_to_ticket(context):
    if context.has_column('tickets', 'muted'):
        return False

    context.operations.add_column(
        'tickets', Column('muted', Boolean, nullable=True))

    for ticket in context.session.query(Ticket):
        ticket.muted = False

    context.session.flush()
    context.operations.alter_column('tickets', 'muted', nullable=False)


@upgrade_task('Add archived flag to ticket')
def add_archived_flag_to_ticket(context):
    if context.has_column('tickets', 'archived'):
        return False

    context.add_column_with_defaults(
        'tickets', Column(
            'archived',
            Boolean,
            nullable=False,
            default=False
        ), default=lambda x: False)


@upgrade_task('Add archived as a state and remove flag')
def add_archived_state_to_ticket(context):
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

    op.execute("""
        ALTER  TABLE tickets ALTER COLUMN state TYPE ticket_state_
        USING state::text::ticket_state_;
    """)

    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(context.operations.get_bind(), checkfirst=False)

    op.execute("""
        ALTER TABLE tickets ALTER COLUMN state TYPE ticket_state
        USING state::text::ticket_state
    """)
    tmp_type.drop(context.operations.get_bind(), checkfirst=False)
