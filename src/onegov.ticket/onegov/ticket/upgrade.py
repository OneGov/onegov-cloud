""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.ticket import Ticket
from sqlalchemy import Column, Text


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
