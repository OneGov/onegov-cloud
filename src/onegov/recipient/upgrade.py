""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task, UpgradeContext


@upgrade_task('Make recipient polymorphic type non-nullable')
def make_recipient_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    if context.has_table('generic_recipients'):
        context.operations.execute("""
            UPDATE generic_recipients SET type = 'generic' WHERE type IS NULL;
        """)

        context.operations.alter_column(
            'generic_recipients', 'type', nullable=False
        )
