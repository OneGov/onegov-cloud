""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.activity import Booking, Period, Occasion
from onegov.core.orm.types import UUID, JSON
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
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


@upgrade_task('Add data column to period')
def add_data_column_to_period(context):
    context.operations.add_column('periods', Column(
        'data', JSON, nullable=True, default=dict
    ))

    for period in context.session.query(Period):
        period.data = {}

    context.session.flush()
    context.operations.alter_column('periods', 'data', nullable=False)


@upgrade_task('Add attendee_count column to occasion')
def add_attendee_count_column_to_occasion(context):
    context.operations.add_column('occasions', Column(
        'attendee_count', Integer, nullable=True, default=0
    ))

    for occasion in context.session.query(Occasion):
        occasion.attendee_count = len(occasion.accepted)

    context.session.flush()
    context.operations.alter_column(
        'occasions', 'attendee_count', nullable=False)


@upgrade_task('Add finalized flag to period')
def add_finalized_flag_to_period(context):
    context.operations.add_column('periods', Column(
        'finalized', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(Period):
        period.finalized = False

    context.session.flush()
    context.operations.alter_column('periods', 'finalized', nullable=False)


@upgrade_task('Add payment model columns')
def add_payment_model_columns(context):
    context.operations.add_column('periods', Column(
        'max_bookings_per_attendee', Integer, nullable=True
    ))

    context.operations.add_column('periods', Column(
        'booking_cost', Numeric(precision=8, scale=2), nullable=True
    ))

    context.operations.add_column('periods', Column(
        'all_inclusive', Boolean, nullable=True
    ))

    for period in context.session.query(Period):
        period.all_inclusive = False

    context.session.flush()
    context.operations.alter_column('periods', 'all_inclusive', nullable=False)

    context.operations.add_column('occasions', Column(
        'cost', Numeric(precision=8, scale=2), nullable=True
    ))

    context.operations.add_column('bookings', Column(
        'cost', Numeric(precision=8, scale=2), nullable=True
    ))


@upgrade_task('Add cancelled flag to occasion')
def add_cancelled_flag_to_occasion(context):
    context.operations.add_column('occasions', Column(
        'cancelled', Boolean, nullable=True
    ))

    for occasion in context.session.query(Occasion):
        occasion.cancelled = False

    context.session.flush()
    context.operations.alter_column('occasions', 'cancelled', nullable=False)
