""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm import Base, find_models
from onegov.core.orm.abstract import Associable
from onegov.core.orm.types import JSON
from sqlalchemy import inspect, text
from sqlalchemy.exc import NoInspectionAvailable


@upgrade_task('Drop primary key from associated tables')
def drop_primary_key_from_associated_tables(context):
    bases = set()

    for cls in find_models(Base, lambda cls: issubclass(cls, Associable)):
        bases.add(cls.association_base())

    for base in bases:
        for link in base.registered_links.values():
            if context.has_table(link.table.name):

                # XXX do not use this kind of statement outside upgrades!
                command = """
                    ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey
                """.format(table=link.table.name)

                context.operations.execute(command)


@upgrade_task('Migrate to JSONB', always_run=True, raw=True)
def migrate_to_jsonb(connection, schemas):
    """ Migrates all text base json columns to jsonb. """

    def json_columns(cls):
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
        classes.extend(find_models(ORMBase, is_match=lambda cls: True))
    except ImportError:
        pass

    columns = list(c for cls in classes for c in json_columns(cls))

    if not columns:
        return False

    text_columns = list(
        r.identity for r in connection.execute(text("""
            SELECT concat_ws(':', table_schema, table_name, column_name)
                AS identity
              FROM information_schema.columns
             WHERE data_type != 'jsonb'
               AND table_schema IN :schemas
               AND column_name IN :names
        """), schemas=tuple(schemas), names=tuple(c.name for c in columns))
    )

    for schema in schemas:
        for column in columns:
            identity = ':'.join((schema, column.table.name, column.name))

            if identity not in text_columns:
                continue

            # XXX do not use this kind of statement outside upgrades!
            connection.execute("""
                ALTER TABLE "{schema}".{table}
                ALTER COLUMN {column}
                TYPE JSONB USING {column}::jsonb
            """.format(
                schema=schema,
                table=column.table.name,
                column=column.name
            ))

            # commits/rolls back the current transaction (to keep the number
            # of required locks to a minimum)
            yield True


@upgrade_task('Rename associated tables')
def rename_associated_tables(context):
    bases = set()

    for cls in find_models(Base, lambda cls: issubclass(cls, Associable)):
        bases.add(cls.association_base())

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
                sql = f'SELECT count(*) FROM {new_name}'
                assert context.session.execute(sql).fetchone().count == 0, f"""
                    Can not rename the associated table "{old_name}" to
                    "{new_name}", the new table "{new_name}" already exists
                    and contains values.
                """
                context.operations.drop_table(new_name)

            if context.has_table(old_name) and not context.has_table(new_name):
                context.operations.rename_table(old_name, new_name)
