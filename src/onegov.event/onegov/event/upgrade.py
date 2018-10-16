""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.event import EventCollection
from sqlalchemy import Column


@upgrade_task('Add coordinates column')
def add_coordinates_column(context):
    for table in ('events', 'event_occurrences'):
        context.operations.add_column(
            table, Column('coordinates', JSON(), nullable=True))


@upgrade_task('Drop coordinates column from occurrences')
def drop_coordinates_column(context):
    context.operations.drop_column('event_occurrences', 'coordinates')


@upgrade_task('Migrate coordinates column in events')
def migrate_coordinates_column(context):
    # merge the separate coordinates column into the content column
    # (gotta love postgres' json support!)
    context.session.execute("""
        UPDATE events
        SET "content" = (
            "content" || (
                '{"coordinates": ' || "coordinates"::text || '}'
            )::jsonb
        )
        WHERE coordinates IS NOT NULL
    """)

    context.operations.drop_column('events', 'coordinates')


@upgrade_task('Validate existing rrules')
def validate_existing_rrules(context):
    for event in EventCollection(context.session).query():
        event.validate_recurrence('recurrence', event.recurrence)
