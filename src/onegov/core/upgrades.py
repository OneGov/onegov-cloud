""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from inspect import isabstract
from itertools import chain
from libres.db.models import ORMBase
from onegov.core.orm.abstract.adjacency_list import AdjacencyList
from onegov.core.upgrade import upgrade_task
from onegov.core.orm import Base, find_models
from onegov.core.orm.abstract import Associable
from onegov.core.orm.types import JSON
from sqlalchemy import inspect, text
from sqlalchemy import Numeric
from sqlalchemy.exc import NoInspectionAvailable


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from onegov.core.orm.abstract.associable import RegisteredLink
    from sqlalchemy import Column
    from sqlalchemy.engine import Connection

    from .upgrade import UpgradeContext


@upgrade_task('Drop primary key from associated tables')
def drop_primary_key_from_associated_tables(context: UpgradeContext) -> None:
    bases = {
        cls.association_base()  # type: ignore[attr-defined]
        for cls in find_models(Base, lambda cls: issubclass(cls, Associable))
    }

    for base in bases:
        for link in base.registered_links.values():
            if context.has_table(link.table.name):

                # XXX do not use this kind of statement outside upgrades!
                command = text("""
                    ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey
                """.format(table=link.table.name))

                context.operations.execute(command)


@upgrade_task('Migrate to JSONB', always_run=True, raw=True)
def migrate_to_jsonb(
    connection: Connection,
    schemas: Sequence[str]
) -> Iterator[bool]:
    """ Migrates all text base json columns to jsonb. """

    def json_columns(cls: type[Any]) -> Iterator[Column[Any]]:
        try:
            for column in inspect(cls).columns:
                if isinstance(column.type, JSON):
                    yield column
        except NoInspectionAvailable:
            pass

    classes = list(find_models(Base, is_match=lambda cls: True))

    # XXX onegov.libres (but not libres itself) uses json with a different orm
    # base - so we need to included it manually
    try:
        from libres.db.models import ORMBase
        classes.extend(find_models(
            # TODO: we should change find_models to operate on
            #       sqlalchemy.orm.DeclarativeBase once we upgrade
            #       to SQLAlchemy 2.0
            ORMBase,  # type: ignore[arg-type]
            is_match=lambda cls: True)
        )
    except ImportError:
        pass

    columns = [c for cls in classes for c in json_columns(cls)]

    if not columns:
        return False  # type:ignore[return-value]

    text_columns = [
        r.identity for r in connection.execute(text("""
            SELECT concat_ws(':', table_schema, table_name, column_name)
                AS identity
              FROM information_schema.columns
             WHERE data_type != 'jsonb'
               AND table_schema IN :schemas
               AND column_name IN :names
        """), schemas=tuple(schemas), names=tuple(c.name for c in columns))
    ]

    for schema in schemas:
        for column in columns:
            identity = f'{schema}:{column.table.name}:{column.name}'

            if identity not in text_columns:
                continue

            # XXX do not use this kind of statement outside upgrades!
            connection.execute(text("""
                ALTER TABLE "{schema}".{table}
                ALTER COLUMN {column}
                TYPE JSONB USING {column}::jsonb
            """.format(
                schema=schema,
                table=column.table.name,
                column=column.name
            )))

            # commits/rolls back the current transaction (to keep the number
            # of required locks to a minimum)
            yield True


@upgrade_task('Rename associated tables')
def rename_associated_tables(context: UpgradeContext) -> None:
    bases = {
        cls.association_base()  # type:ignore[attr-defined]
        for cls in find_models(Base, lambda cls: issubclass(cls, Associable))
    }

    for base in bases:
        for link in base.registered_links.values():
            new_name = link.table.name
            old_name = new_name[:new_name.rfind(link.attribute)].rstrip('_')
            if new_name == old_name:
                continue

            if context.has_table(old_name) and context.has_table(new_name):
                # We expect that the ORM already created the new tables at this
                # point while still having the old one - we therefore drop the
                # newly created table (which should be empty at this time).
                sql = text(f'SELECT count(*) FROM {new_name}')
                assert context.session.execute(sql).fetchone().count == 0, f"""
                    Can not rename the associated table "{old_name}" to
                    "{new_name}", the new table "{new_name}" already exists
                    and contains values.
                """
                context.operations.drop_table(new_name)

            if context.has_table(old_name) and not context.has_table(new_name):
                context.operations.rename_table(old_name, new_name)


@upgrade_task('OGC-1792 Remove all wtfs tables')
def remove_all_wtfs_tables(context: UpgradeContext) -> None:
    tables = ['wtfs_payment_type', 'wtfs_pickup_dates', 'wtfs_scan_jobs']

    for table in tables:
        if context.has_table(table):
            context.operations.drop_table(table)


@upgrade_task('Remove redundant page to general file links')
def remove_redundant_page_to_general_file_links(
    context: UpgradeContext
) -> None:

    if not context.has_table('files_for_pages_files'):
        return

    duplicate_pairs = [
        {'file_id': file_id, 'pages_id': pages_id}
        for file_id, pages_id in context.session.execute(text("""
            SELECT file_id, pages_id FROM (
                SELECT COUNT(*) as cnt, file_id, pages_id
                  FROM files_for_pages_files
                 GROUP BY file_id, pages_id
            ) AS t
            WHERE t.cnt > 1
        """))
    ]

    if not duplicate_pairs:
        return

    # delete all the links with duplicate entries
    context.session.execute(text("""
        DELETE
          FROM files_for_pages_files
         WHERE file_id = :file_id
           AND pages_id = :pages_id
    """), duplicate_pairs)

    # then reinsert a single link per duplicate entry
    context.session.execute(text("""
        INSERT INTO files_for_pages_files (file_id, pages_id)
        VALUES (:file_id, :pages_id)
    """), duplicate_pairs)


@upgrade_task('Add unique constraint to association tables')
def unique_constraint_in_association_tables(context: UpgradeContext) -> None:
    bases = {
        cls.association_base()  # type:ignore[attr-defined]
        for cls in chain(
            find_models(Base, lambda cls: issubclass(cls, Associable)),
            find_models(ORMBase, lambda cls: issubclass(cls, Associable))
        )
    }

    link: RegisteredLink
    for base in bases:
        for link in base.registered_links.values():
            if context.has_table(table := link.table.name):
                key, association_key = link.table.c.keys()
                # NOTE: We can't use operations.create_index
                #       because we want to emit IF NOT EXISTS
                #       and we're currently on SQLAlchemy <1.4
                context.operations.execute(text(f"""
                    CREATE UNIQUE INDEX
                    IF NOT EXISTS "uq_assoc_{table}"
                    ON "{table}" ("{key}", "{association_key}")
                """))


@upgrade_task(
    'Change order to Numeric to avoid re-sorting siblings on every new item'
)
def change_adjacency_list_order_to_numeric(context: UpgradeContext) -> None:
    def is_concrete_subclass(cls: type) -> bool:
        return (
            issubclass(cls, AdjacencyList)
            and cls is not AdjacencyList
            and not isabstract(cls)
        )

    table_names: set[str] = {
        cls.__tablename__  # type: ignore[attr-defined]
        for cls in chain(
            find_models(Base, is_concrete_subclass),
            find_models(ORMBase, is_concrete_subclass),
        )
    }

    for table_name in table_names:
        if context.has_table(table_name):
            context.operations.alter_column(
                table_name,
                'order',
                type_=Numeric(30, 15),
                postgresql_using='"order"::numeric'
            )


@upgrade_task('Drop remaining gazette and notices tables')
def drop_remaining_gazette_and_notices_tables(context: UpgradeContext) -> None:
    for table in (
        'files_for_gazette_issues_files',
        'files_for_official_notices_files',
        'gazette_categories',
        'gazette_issues',
        'gazette_organizations',
        'official_notices',
    ):
        if context.has_table(table):
            context.operations.drop_table(table)
