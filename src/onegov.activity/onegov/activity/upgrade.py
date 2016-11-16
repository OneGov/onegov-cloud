""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.activity import Booking, Period
from onegov.core.orm.types import UUID
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Boolean, Column, Enum, ForeignKey
from sqlalchemy.orm import joinedload


@upgrade_task('Rebuild bookings')
def rebuild_bookings(context):
    # having not created any bookings yet, we can rebuild them
    context.operations.drop_table('bookings')


@upgrade_task('Add period_id to bookings')
def add_period_id_to_bookings(context):

    context.operations.add_column('bookings', Column(
        'period_id', UUID, ForeignKey("periods.id"), nullable=True
    ))

    bookings = context.session.query(Booking)
    bookings = bookings.options(joinedload(Booking.occasion))

    for booking in bookings:
        booking.period_id = booking.occasion.period_id

    context.session.flush()
    context.operations.alter_column('bookings', 'period_id', nullable=False)


@upgrade_task('Change booking states')
def change_booking_states(context):

    new_type = Enum(
        'open',
        'blocked',
        'accepted',
        'denied',
        'cancelled',
        name='booking_state'
    )

    op = context.operations

    op.execute("""
        ALTER TABLE bookings ALTER COLUMN state TYPE Text;
        UPDATE bookings SET state = 'open' WHERE state = 'unconfirmed';
        DROP TYPE booking_state;
    """)

    new_type.create(op.get_bind())

    op.execute("""
        ALTER TABLE bookings ALTER COLUMN state
        TYPE booking_state USING state::text::booking_state;
    """)


@upgrade_task('Add confirmed flag to period')
def add_confirmed_flag_to_period(context):
    context.operations.add_column('periods', Column(
        'confirmed', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(Period):
        period.confirmed = False

    context.session.flush()
    context.operations.alter_column('periods', 'confirmed', nullable=False)
