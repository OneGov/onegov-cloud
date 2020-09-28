""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column, ARRAY, Text, Boolean

from onegov.core.upgrade import upgrade_task


@upgrade_task('Change withholding tax column to boolean')
def change_withholding_tax_column_type(context):
    if context.has_column('translators', 'withholding_tax'):
        context.operations.execute(
            'ALTER TABLE translators '
            'ALTER COLUMN withholding_tax TYPE BOOLEAN '
            'USING false'
        )


@upgrade_task('Adds expertise columns')
def add_expertise_columns(context):
    table = 'translators'
    new_cols = (
        'expertise_interpreting_types', 'expertise_professional_guilds'
    )
    for col_name in new_cols:
        if not context.has_column(table, col_name):
            context.add_column_with_defaults(
                table=table,
                column=Column(col_name, ARRAY(Text)),
                default=lambda x: []
            )


@upgrade_task('Adds imported tag for translators')
def add_imported_column(context):
    if not context.has_column('translators', 'imported'):
        context.add_column_with_defaults(
            table='translators',
            column=Column('imported', Boolean, nullable=False),
            default=lambda x: False)
