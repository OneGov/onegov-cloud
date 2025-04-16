""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.orm.types import JSON, UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.ticket import Ticket
from sqlalchemy import Boolean, Column, Integer, Text, Enum
from sqlalchemy import column, update, func, and_, true, false
from sqlalchemy.dialects.postgresql import HSTORE

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


@upgrade_task('Add tags column and index to ticket')
def add_tags_column_and_index_to_ticket(context: UpgradeContext) -> None:
    if context.has_column('tickets', 'tags'):
        return

    context.operations.add_column(
        'tickets', Column('tags', HSTORE, nullable=True)
    )

    context.operations.create_index(
        'ix_tickets_tags',
        'tickets',
        ['tags'],
        postgresql_using='gin',
    )
