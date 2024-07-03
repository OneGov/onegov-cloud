""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add payment types')
def add_payment_types(context: 'UpgradeContext') -> None:
    session = context.session

    if context.has_table('wtfs_payment_type'):
        query = session.execute('SELECT count(*) FROM wtfs_payment_type')
        if not query.scalar():
            session.execute("""
                INSERT INTO wtfs_payment_type ("name", "price_per_quantity")
                VALUES ('normal', 700), ('spezial', 850);
            """)

            query = session.execute("""
                UPDATE groups
                SET meta = CASE
                    WHEN meta @> '{"_price_per_quantity"\\:850}'::jsonb
                    THEN jsonb_set(meta, '{payment_type}', '"spezial"')
                    ELSE jsonb_set(meta, '{payment_type}', '"normal"')
                END
                WHERE groups.meta ? '_price_per_quantity';
            """)
