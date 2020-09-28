""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('Change withholding tax column to boolean')
def change_withholding_tax_column_type(context):
    if context.has_column('translators', 'withholding_tax'):
        context.operations.execute(
            'ALTER TABLE translators '
            'ALTER COLUMN withholding_tax TYPE BOOLEAN '
            'USING false'
        )
