""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.activity.models import Activity, Occasion
from onegov.core.upgrade import upgrade_task
from psycopg2.extras import NumericRange
from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY, INT4RANGE


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


@upgrade_task('Add reporter column')
def add_reporter_column(context):
    context.operations.add_column('activities', Column(
        'reporter', Text, nullable=True))

    for activity in context.session.query(Activity).all():
        activity.reporter = activity.username

    context.session.flush()

    context.operations.alter_column('activities', 'reporter', nullable=True)


@upgrade_task('Add archived state to occasions')
def add_archive_state(context):

    # ALTER TYPE statements don't work inside of transactions -> if you reuse
    # this code, do not put it inside an update that has other things going
    # on!
    connection = context.operations.get_bind()
    previous_isolation_level = connection.get_isolation_level()
    connection.execution_options(isolation_level='AUTOCOMMIT')

    try:
        context.operations.execute(
            "ALTER TYPE occasion_state ADD VALUE IF NOT EXISTS 'archived'")
    finally:
        connection.execution_options(isolation_level=previous_isolation_level)


@upgrade_task('Add start before end constraint to occasions')
def add_start_before_end_constraint_to_occasions(context):

    context.operations.create_check_constraint(
        "start_before_end",
        "occasions",
        '"start" <= "end"'
    )


@upgrade_task('Add occasion durations')
def add_occasion_durations(context):

    context.operations.add_column(
        'activities', Column('durations', Integer, nullable=True, default=0))

    # force an update of all occasions
    for occasion in context.session.query(Occasion).all():
        occasion.note = occasion.note and occasion.note + ' ' or ' '

    context.session.flush()


@upgrade_task('Add occasion durations (second step)')
def add_occasion_durations_second_step(context):

    # undo the damage from the last step
    for occasion in context.session.query(Occasion).all():
        occasion.note = occasion.note and occasion.note.strip() or None

    context.session.flush()


@upgrade_task('Add activity ages')
def add_activity_ages(context):

    context.operations.add_column(
        'activities', Column('ages', ARRAY(INT4RANGE), default=list))

    # force an update of all occasions
    for occasion in context.session.query(Occasion).all():
        occasion.note = occasion.note and occasion.note + ' ' or ' '

    context.session.flush()


@upgrade_task('Add activity ages (second step)')
def add_activity_ages_second_step(context):

    # undo the damage from the last step
    for occasion in context.session.query(Occasion).all():
        occasion.note = occasion.note and occasion.note.strip() or None

    context.session.flush()
