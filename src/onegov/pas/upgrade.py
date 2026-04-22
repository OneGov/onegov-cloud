"""Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from sqlalchemy import Boolean, Column, Text, UUID, text
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task, UpgradeContext


@upgrade_task('Add external id from api 2')
def add_external_id_for_api(context: UpgradeContext) -> None:
    for table in (
        'pas_parliamentarians',
        'pas_parties',
        'pas_parliamentary_groups',
        'pas_commissions',
    ):
        if not context.has_column(table, 'external_kub_id'):
            context.operations.add_column(
                table,
                Column(
                    'external_kub_id',
                    UUID,
                    nullable=True,
                    unique=True,
                ),
            )


@upgrade_task('Add party column to pas_parliamentarians')
def add_party_column_to_pas_parliamentarians(context: UpgradeContext) -> None:
    if context.has_table('pas_parliamentarians'):
        if not context.has_column('pas_parliamentarians', 'party'):
            context.operations.add_column(
                'pas_parliamentarians',
                Column(
                    'party',
                    Text,
                    nullable=True
                )
            )


@upgrade_task('Add import_type column to pas_import_logs')
def add_import_type_column_to_pas_import_logs(context: UpgradeContext) -> None:
    if context.has_table('pas_import_logs'):
        if not context.has_column('pas_import_logs', 'import_type'):
            context.add_column_with_defaults(
                'pas_import_logs',
                Column(
                    'import_type',
                    Text,
                    nullable=False
                ),
                default='automatic'
            )


@upgrade_task('Add district column to par_parliamentarians')
def add_district_column_to_pas_parliamentarians(
        context: UpgradeContext
) -> None:
    if context.has_table('par_parliamentarians'):
        if not context.has_column('par_parliamentarians', 'district'):
            context.add_column_with_defaults(
                'par_parliamentarians',
                Column('district', Text),
                default=None  # type: ignore[arg-type]
            )


@upgrade_task('Add bulk_edit_id column to par_attendence')
def add_bulk_edit_id_column_to_par_attendence(context: UpgradeContext) -> None:
    if context.has_table('par_attendence'):
        if not context.has_column('par_attendence', 'bulk_edit_id'):
            context.operations.add_column(
                'par_attendence',
                Column(
                    'bulk_edit_id',
                    UUID,
                    nullable=True
                )
            )


@upgrade_task('Add source data columns to pas_import_logs')
def add_source_data_columns_to_pas_import_logs(
        context: UpgradeContext
) -> None:
    if context.has_table('pas_import_logs'):
        for column_name in (
            'people_source',
            'organizations_source',
            'memberships_source'
        ):
            if not context.has_column('pas_import_logs', column_name):
                context.operations.add_column(
                    'pas_import_logs',
                    Column(
                        column_name,
                        JSON,
                        nullable=True
                    )
                )


@upgrade_task('Add abschluss column to par_attendence')
def add_abschluss_column_to_par_attendence(context: UpgradeContext) -> None:
    if context.has_table('par_attendence'):
        if not context.has_column('par_attendence', 'abschluss'):
            context.add_column_with_defaults(
                'par_attendence',
                Column(
                    'abschluss',
                    Boolean,
                    nullable=False
                ),
                default=False
            )


@upgrade_task('Add closed column to pas_settlements')
def add_closed_column_to_pas_settlements(context: UpgradeContext) -> None:
    if context.has_table('pas_settlements'):
        if not context.has_column('pas_settlements', 'closed'):
            context.add_column_with_defaults(
                'pas_settlements',
                Column(
                    'closed',
                    Boolean,
                    nullable=False
                ),
                default=False
            )


@upgrade_task('Drop active column from pas_settlements')
def drop_active_column_from_pas_settlements(context: UpgradeContext) -> None:
    if context.has_table('pas_settlements'):
        if context.has_column('pas_settlements', 'active'):
            context.operations.drop_column('pas_settlements', 'active')


@upgrade_task('Tie allowances to settlement runs, drop quarter')
def tie_allowances_to_settlement_runs(
    context: UpgradeContext,
) -> None:
    table = 'pas_presidential_allowances'
    if not context.has_table(table):
        return

    # Delete orphan rows that have no settlement run
    if context.has_column(table, 'settlement_run_id'):
        context.session.execute(
            text(
                f'DELETE FROM {table}'
                f' WHERE settlement_run_id IS NULL'
            )
        )

    # Drop the old unique constraint
    if context.has_column(table, 'quarter'):
        context.operations.drop_constraint(
            'pas_presidential_allowances_year_quarter_role_key',
            table,
        )

    # Drop year and quarter columns
    if context.has_column(table, 'year'):
        context.operations.drop_column(table, 'year')
    if context.has_column(table, 'quarter'):
        context.operations.drop_column(table, 'quarter')

    # Make settlement_run_id non-nullable
    if context.has_column(table, 'settlement_run_id'):
        context.operations.alter_column(
            table,
            'settlement_run_id',
            nullable=False,
        )


@upgrade_task('Add indexes to par_attendence')
def add_indexes_to_par_attendence(context: UpgradeContext) -> None:
    if not context.has_table('par_attendence'):
        return

    for col in ('date', 'parliamentarian_id', 'commission_id', 'type'):
        context.operations.create_index(
            f'ix_par_attendence_{col}',
            'par_attendence',
            [col],
            if_not_exists=True,
        )
