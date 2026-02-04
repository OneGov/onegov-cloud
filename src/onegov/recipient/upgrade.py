""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task, UpgradeContext
from sqlalchemy import text


@upgrade_task('Make recipient polymorphic type non-nullable')
def make_recipient_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    if context.has_table('generic_recipients'):
        context.operations.execute(text("""
            UPDATE generic_recipients SET type = 'generic' WHERE type IS NULL;
        """))

        context.operations.alter_column(
            'generic_recipients', 'type', nullable=False
        )
