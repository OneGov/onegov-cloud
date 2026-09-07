""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from onegov.core.orm.types import JSON, UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.directory import Directory
from onegov.directory.models import DirectoryEntry
from onegov.form.parser import ParsedForm
from onegov.form.orm_types import Formcode
from sqlalchemy import Column, Integer, Text, UUID, bindparam, text
from sqlalchemy.orm import joinedload


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


@upgrade_task('Add meta and content columns to entry recipients')
def add_meta_data_and_content_columns_to_entry_recipients(
    context:
    UpgradeContext
) -> None:
    if not context.has_column('entry_recipients', 'meta'):
        context.operations.add_column('entry_recipients',
                                      Column('meta', JSON()))

    if not context.has_column('entry_recipients', 'content'):
        context.operations.add_column('entry_recipients',
                                      Column('content', JSON))


@upgrade_task('Add content hash to directory entries')
def add_content_hash_to_directory_entries(context: UpgradeContext) -> None:
    if context.has_column('directory_entries', 'content_hash'):
        return

    context.operations.add_column(
        'directory_entries',
        Column('content_hash', Text, nullable=True)
    )


@upgrade_task('Calc content hash for directory entries')
def calc_content_hash_for_directory_entries(context: UpgradeContext) -> None:
    if not context.has_column('directory_entries', 'content_hash'):
        return

    entries = (
        context.session.query(DirectoryEntry)
        .filter(DirectoryEntry.content_hash.is_(None))
        .options(joinedload(DirectoryEntry.files))
    )

    for entry in entries:
        entry.update_content_hash()

        # Write only content_hash via raw SQL so modified is never touched,
        # then expire the entry so the ORM doesn't re-flush the dirty state.
        context.session.execute(
            text('UPDATE directory_entries SET content_hash = :hash'
                 ' WHERE id = :id'),
            {'hash': entry.content_hash, 'id': entry.id}
        )
        context.session.expire(entry)


@upgrade_task('Switch to JSON serialized form structure')
def directories_switch_to_parsed_form(context: UpgradeContext) -> None:
    if not context.has_table('directories'):
        return

    # no migration needed, the old column is already gone
    if not context.has_column('directories', 'structure'):
        return

    # first add the new column, but make it nullable
    context.operations.add_column(
        'directories',
        Column('parsed_structure', Formcode, nullable=True)
    )

    # bulk update the table with the parsed definitions
    if values := [
        {
            'id': directory_id,
            'parsed': ParsedForm.from_formcode(definition),
        }
        for directory_id, definition in context.session.execute(text(
            'SELECT id, structure FROM directories'
        ))
    ]:
        context.session.execute(text("""
            UPDATE directories
               SET parsed_structure = :parsed
             WHERE id = :id
        """).bindparams(
            bindparam('id', type_=UUID),
            bindparam('parsed', type_=Formcode)
        ), values)

    # finally make the column not nullable and remove the old column
    context.operations.alter_column(
        'directories', 'parsed_structure', nullable=False)
    context.operations.drop_column('directories', 'structure')
