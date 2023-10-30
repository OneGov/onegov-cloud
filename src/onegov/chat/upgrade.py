""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Text


@upgrade_task('Add messages column and remove others1')
def add_messages_column_and_remove_others1(context):
    if not context.has_column('chats', 'messages'):
        context.operations.add_column('chats', Column('messages', Text))
    if context.has_column('chats', 'publication_start'):
        context.operations.drop_column('chats', 'publication_start')
    if context.has_column('chats', 'publication_end'):
        context.operations.drop_column('chats', 'publication_end')
    if context.has_column('chats', ' type'):
        context.operations.drop_column('chats', ' type')
