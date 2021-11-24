""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column, Boolean

from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task


@upgrade_task('Change withholding tax column to boolean')
def change_withholding_tax_column_type(context):
    if not context.has_table('translators'):
        return
    if context.has_column('translators', 'withholding_tax'):
        context.operations.execute(
            'ALTER TABLE translators '
            'ALTER COLUMN withholding_tax TYPE BOOLEAN '
            'USING false'
        )


@upgrade_task('Adds meta and content columns')
def add_meta_content_columns(context):
    if not context.has_table('translators'):
        return
    table = 'translators'
    new_cols = ('meta', 'content')
    for col_name in new_cols:
        if not context.has_column(table, col_name):
            context.add_column_with_defaults(
                table=table,
                column=Column(col_name, JSON, nullable=False),
                default=lambda x: {}
            )


@upgrade_task('Adds imported tag for translators')
def add_imported_column(context):
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'imported'):
        context.add_column_with_defaults(
            table='translators',
            column=Column('imported', Boolean, nullable=False),
            default=lambda x: False
        )


@upgrade_task('Add self-employed column')
def add_self_employed_column(context):
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'self_employed'):
        context.add_column_with_defaults(
            table='translators',
            column=Column('self_employed', Boolean),
            default=lambda x: False
        )
