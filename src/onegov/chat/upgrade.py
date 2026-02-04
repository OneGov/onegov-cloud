""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task
from sqlalchemy import text, Column, Text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add messages column and remove others1')
def add_messages_column_and_remove_others1(context: UpgradeContext) -> None:
    if not context.has_column('chats', 'messages'):
        context.operations.add_column('chats', Column('messages', Text))
    if context.has_column('chats', 'publication_start'):
        context.operations.drop_column('chats', 'publication_start')
    if context.has_column('chats', 'publication_end'):
        context.operations.drop_column('chats', 'publication_end')
    if context.has_column('chats', ' type'):
        context.operations.drop_column('chats', ' type')

    return None


@upgrade_task('Make Message.type not nullable')
def make_message_type_not_nullable(context: UpgradeContext) -> None:
    if not context.has_table('messages'):
        return

    if context.has_column('messages', 'type'):
        context.operations.execute(text("""
            UPDATE messages
               SET type = 'generic'
             WHERE type IS NULL;
        """))
        context.operations.alter_column('messages', 'type', nullable=False)
