""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from contextlib import contextmanager
from onegov.activity import Booking
from onegov.core.orm.types import UUID
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column, ForeignKey
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


@upgrade_task('Add additional states to bookings')
def add_additional_states_to_bookings(context):

    # ALTER TYPE statements don't work inside of transactions -> if you reuse
    # this code, do not put it inside an update that has other things going
    # on!
    type_name = 'booking_state'
    states = ('blocked', 'denied')

    @contextmanager
    def temporary_isolation_level(isolation_level):
        connection = context.operations.get_bind()
        previous_isolation_level = connection.get_isolation_level()
        connection.execution_options(isolation_level=isolation_level)

        yield

        connection.execution_options(isolation_level=previous_isolation_level)

    with temporary_isolation_level('AUTOCOMMIT'):
        for state in states:
            context.operations.execute(
                "ALTER TYPE {} ADD VALUE IF NOT EXISTS '{}'".format(
                    type_name, state)
            )
