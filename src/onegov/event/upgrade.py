""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.event import Event, EventCollection
from sqlalchemy import text, Column


from typing import Any


@upgrade_task('Add coordinates column')
def add_coordinates_column(context: UpgradeContext) -> None:
    for table in ('events', 'event_occurrences'):
        context.operations.add_column(
            table, Column('coordinates', JSON(), nullable=True))


@upgrade_task('Drop coordinates column from occurrences')
def drop_coordinates_column(context: UpgradeContext) -> None:
    context.operations.drop_column('event_occurrences', 'coordinates')


@upgrade_task('Migrate coordinates column in events')
def migrate_coordinates_column(context: UpgradeContext) -> None:
    # merge the separate coordinates column into the content column
    # (gotta love postgres' json support!)
    context.session.execute(text("""
        UPDATE events
        SET "content" = (
            "content" || (
                '{"coordinates": ' || "coordinates"::text || '}'
            )::jsonb
        )
        WHERE coordinates IS NOT NULL
    """))

    context.operations.drop_column('events', 'coordinates')


@upgrade_task('Validate existing rrules')
def validate_existing_rrules(context: UpgradeContext) -> None:
    for event in EventCollection(context.session).query():
        event.validate_recurrence('recurrence', event.recurrence)


@upgrade_task('Add meta data and content columns to occurrences')
def add_meta_data_and_content_columns_to_occurrences(
    context: UpgradeContext
) -> None:

    table = 'event_occurrences'
    if not context.has_column(table, 'meta'):
        context.operations.add_column(table, Column('meta', JSON()))

    if not context.has_column(table, 'content'):
        context.operations.add_column(table, Column('content', JSON()))


@upgrade_task('Migrate filter_keywords column in events')
def migrate_filter_keywords_column(context: UpgradeContext) -> None:
    data: list[dict[str, Any]] = []
    # first retrieve all the stored keywords and normalize them
    for event_id, keywords in context.session.execute(text("""
        SELECT id, "content"->'filter_keywords' AS filter_keywords
        FROM events
        WHERE "content" ? 'filter_keywords'
    """)):
        if not keywords:
            continue

        for keyword, values in keywords.items():
            if values is None:
                continue
            if isinstance(values, str):
                values = [values]
            for value in values:
                if value is None:
                    continue
                data.append({
                    'event_id': event_id,
                    'keyword': keyword,
                    'value': value
                })

    # then perform a bulk-insert into the new table
    if data:
        context.session.execute(text("""
            INSERT INTO event_filter_values ("event_id", "keyword", "value")
            VALUES (:event_id, :keyword, :value)
        """), data)

    # then remove the redundant data from the events/occurrence tables
    context.session.execute(text("""
        UPDATE events
        SET content = content - 'filter_keywords'
        WHERE "content" ? 'filter_keywords'
    """))
    context.session.execute(text("""
        UPDATE event_occurrences
        SET content = content - 'filter_keywords'
        WHERE "content" ? 'filter_keywords'
    """))


@upgrade_task('Remove namespace from cross-namespace fetch sources')
def remove_namespace_from_cross_namespace_fetch_sources(
    context: UpgradeContext
) -> None:
    if not context.has_table('events'):
        return

    own_namespace = context.app.namespace
    for schema in context.app.session_manager.list_schemas():
        if '-' not in schema:
            continue

        namespace, entity = schema.split('-', 1)
        if namespace == own_namespace:
            continue

        old_prefix = f'fetch-{namespace}-{entity}-'
        new_prefix = f'fetch-{entity}-'

        stale_ids = [
            stale_id for stale_id, in context.session.execute(text("""
                SELECT stale.id
                FROM events stale
                JOIN events renamed
                ON left(renamed.meta->>'source', :length) = :old_prefix
                AND stale.meta->>'source' = :new_prefix
                    || substr(renamed.meta->>'source', :length + 1)
            """), {
                'old_prefix': old_prefix,
                'new_prefix': new_prefix,
                'length': len(old_prefix),
            })
        ]
        if stale_ids:
            query = context.session.query(Event)
            query = query.filter(Event.id.in_(stale_ids))
            for event in query:
                context.session.delete(event)
            context.session.flush()

        context.session.execute(text("""
            UPDATE events
            SET meta = jsonb_set(
                meta,
                '{source}',
                to_jsonb(
                    :new_prefix || substr(meta->>'source', :length + 1)
                )
            )
            WHERE left(meta->>'source', :length) = :old_prefix
        """), {
            'old_prefix': old_prefix,
            'new_prefix': new_prefix,
            'length': len(old_prefix),
        })


@upgrade_task('Add indexes to speed up occurrence filters')
def add_indexes_to_speed_up_occurrence_filters(
    context: UpgradeContext
) -> None:
    if context.has_table('event_occurrences'):
        context.operations.create_index(
            'ix_event_occurrences_event_id',
            'event_occurrences',
            ['event_id'],
            if_not_exists=True
        )
        context.operations.create_index(
            'ix_event_occurrences_start',
            'event_occurrences',
            ['start'],
            if_not_exists=True
        )
        context.operations.create_index(
            'ix_event_occurrences_end',
            'event_occurrences',
            ['end'],
            if_not_exists=True
        )
        context.operations.create_index(
            'ix_event_occurrences_tags',
            'event_occurrences',
            ['tags'],
            postgresql_using='gist',
            if_not_exists=True
        )
