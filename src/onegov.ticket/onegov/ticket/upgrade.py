""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.ticket import Ticket
from sqlalchemy import Column, Text


@upgrade_task('Add handler_id to ticket', always_run=True)
def add_handler_id_to_ticket(context):

    if not context.has_column('tickets', 'handler_id'):
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
