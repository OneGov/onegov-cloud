""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('rename tickets column group to group_name')
def rename_tickets_column_group_to_group_name(context):
    # Renaming the column group to group_name as 'group' is a reserved word
    # in postgres and reindexing fails while generating the tsvector string

    if context.has_column('tickets', 'group'):
        context.session.execute("""
            ALTER TABLE tickets
            RENAME COLUMN group to group_name;
        """)
