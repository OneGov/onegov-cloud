""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task, UpgradeContext
from sqlalchemy import Column, Boolean, Enum, Text


@upgrade_task('Change withholding tax column to boolean')
def change_withholding_tax_column_type(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if context.has_column('translators', 'withholding_tax'):
        context.operations.execute(
            'ALTER TABLE translators '
            'ALTER COLUMN withholding_tax TYPE BOOLEAN '
            'USING false'
        )


@upgrade_task('Adds meta and content columns')
def add_meta_content_columns(context: UpgradeContext) -> None:
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
def add_imported_column(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'imported'):
        context.add_column_with_defaults(
            table='translators',
            column=Column('imported', Boolean, nullable=False),
            default=lambda x: False
        )


@upgrade_task('Add self-employed column')
def add_self_employed_column(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'self_employed'):
        context.add_column_with_defaults(
            table='translators',
            column=Column('self_employed', Boolean),
            default=lambda x: False
        )


@upgrade_task('Add unique constraint to translator email')
def add_unique_constraint_to_translator_email(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if context.has_column('translators', 'email'):
        context.operations.execute(
            "UPDATE translators SET email=NULL WHERE email='';"
        )
        context.operations.create_unique_constraint(
            'unique_translators_email', 'translators', ['email']
        )


@upgrade_task('Add translator type')
def add_translator_type(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'state'):
        state = Enum('proposed', 'published', name='translator_state')
        if not context.has_enum('translator_state'):
            state.create(context.operations.get_bind())
        context.add_column_with_defaults(
            table='translators',
            column=Column('state', state, nullable=False, default='published'),
            default=lambda x: 'published'
        )


@upgrade_task('Add translator profession')
def add_translator_profession(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'profession'):
        context.operations.add_column(
            'translators',
            Column('profession', Text)
        )


@upgrade_task('Moves the hometown field onto the translator itself.')
def add_hometown(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'hometown'):
        context.operations.add_column(
            'translators',
            Column('hometown', Text)
        )


@upgrade_task('Remove old unused column translator nationality')
def remove_nationality_column(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if context.has_column('translators', 'nationality'):
        context.operations.drop_column('translators', 'nationality')


@upgrade_task('Add personal number column')
def add_personal_number_column(context: UpgradeContext) -> None:
    if not context.has_table('translators'):
        return
    if not context.has_column('translators', 'personal_number'):
        context.operations.add_column(
            'translators', Column('personal_number', Text)
        )
