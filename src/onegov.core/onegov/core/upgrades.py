""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm import Base, find_models
from onegov.core.orm.abstract import Associable


@upgrade_task('Drop primary key from associated tables')
def drop_primary_key_from_associated_tables(context):
    bases = set()

    for cls in find_models(Base, lambda cls: issubclass(cls, Associable)):
        bases.add(cls.association_base())

    for base in bases:
        for link in base.registered_links.values():
            if context.has_table(link.table.name):

                command = """
                    ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey
                """.format(table=link.table.name)

                context.operations.execute(command)
