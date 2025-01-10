""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column, Integer

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.directory import Directory


@upgrade_task('Add entries count')
def add_entries_count(context: UpgradeContext) -> None:
    if context.has_column('directories', 'count'):
        return

    context.operations.add_column('directories', Column(
        'count', Integer, nullable=True
    ))

    context.session.flush()

    for directory in context.session.query(Directory):
        directory.count = len(directory.entries)

    context.session.flush()

    context.operations.alter_column('directories', 'count', nullable=False)


@upgrade_task('Update ordering')
def update_ordering(context: UpgradeContext) -> None:
    for directory in context.session.query(Directory):
        config = directory.configuration

        for entry in directory.entries:
            entry.order = config.extract_order(entry.values)


@upgrade_task('Make external link visible by default')
def make_external_link_visible_by_default(context: UpgradeContext) -> None:
    for directory in context.session.query(Directory):
        directory.configuration.link_visible = True


@upgrade_task('Adds publication dates to directory entries')
def add_publication_dates_to_dir_entries(context: UpgradeContext) -> None:
    if not context.has_column('directory_entries', 'publication_start'):
        context.operations.add_column(
            'directory_entries',
            Column('publication_start', UTCDateTime, nullable=True)
        )
    if not context.has_column('directory_entries', 'publication_end'):
        context.operations.add_column(
            'directory_entries',
            Column('publication_end', UTCDateTime, nullable=True)
        )


@upgrade_task('Make directory models polymorphic type non-nullable')
def make_directory_models_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    for table in ('directories', 'directory_entries'):
        if context.has_table(table):
            context.operations.execute(f"""
                UPDATE {table} SET type = 'generic' WHERE type IS NULL;
            """)

            context.operations.alter_column(table, 'type', nullable=False)
