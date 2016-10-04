""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.activity.models import Occasion
from onegov.core.upgrade import upgrade_task
from psycopg2.extras import NumericRange
from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import INT4RANGE


@upgrade_task('Redesign occasion table')
def redesign_occasion_table(context):
    context.operations.drop_column('occasions', 'booking_start')
    context.operations.drop_column('occasions', 'min_age')
    context.operations.drop_column('occasions', 'max_age')
    context.operations.drop_column('occasions', 'spots')

    context.operations.add_column('occasions', Column(
        'note', Text, nullable=True))

    context.operations.add_column('occasions', Column(
        'age', INT4RANGE, nullable=True))

    context.operations.add_column('occasions', Column(
        'spots', INT4RANGE, nullable=True))

    for occasion in context.session.query(Occasion).all():
        occasion.age = NumericRange(6, 17, bounds='[]')
        occasion.spots = NumericRange(0, 10, bounds='[]')

    context.session.flush()

    context.operations.alter_column('occasions', 'spots', nullable=False)
    context.operations.alter_column('occasions', 'age', nullable=False)


@upgrade_task('Make occasion location optional')
def make_occasion_location_optional(context):
    context.operations.alter_column('occasions', 'location', nullable=True)


@upgrade_task('Ensure occasions/bookings cannot be orphaned')
def ensure_occasions_bookings_cannot_be_orphaned(context):
    context.operations.alter_column('occasions', 'activity_id', nullable=False)
    context.operations.alter_column('bookings', 'occasion_id', nullable=False)
