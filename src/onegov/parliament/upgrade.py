"""Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Text

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext


@upgrade_task('Introduce parliament module: rename pas tables')
def introduce_parliament_module_rename_pas_tables(
    context: UpgradeContext
) -> None:
    for current_name, target_name in (
        ('pas_attendence', 'par_attendence'),
        ('pas_changes', 'par_changes'),
        ('pas_commission_memberships', 'par_commission_memberships'),
        ('pas_commissions', 'par_commissions'),
        ('pas_legislative_periods', 'par_legislative_periods'),
        ('pas_parliamentarian_roles', 'par_parliamentarian_roles'),
        ('pas_parliamentarians', 'par_parliamentarians'),
        ('pas_parliamentary_groups', 'par_parliamentary_groups'),
        ('pas_parties', 'par_parties'),
    ):

        if context.has_table(current_name):
            if context.has_table(target_name):
                # target may was created by defining the table in the model
                context.operations.execute(
                    f'DROP TABLE IF EXISTS {target_name} CASCADE'
                )

            context.operations.rename_table(
                current_name, target_name)


@upgrade_task('Add type column to parliament models')
def add_type_column_to_parliament_models(
    context: UpgradeContext
) -> None:
    for table, type_name, poly_type in (
        ('par_attendence', 'poly_type', 'pas_attendence'),
        ('par_changes', 'type', 'pas_change'),
        ('par_commission_memberships', 'type', 'pas_commission_membership'),
        ('par_commissions', 'poly_type', 'pas_commission'),
        ('par_legislative_periods', 'type', 'pas_legislative_period'),
        ('par_parliamentarian_roles', 'type', 'pas_parliamentarian_role'),
        ('par_parliamentarians', 'type', 'pas_parliamentarian'),
        ('par_parliamentary_groups', 'type', 'pas_parliamentary_group'),
        ('par_parties', 'type', 'pas_party'),
    ):
        if not context.has_column(table, type_name):
            context.operations.add_column(
                table,
                Column(type_name, Text, nullable=True)
            )

            context.operations.execute(
                f"UPDATE {table} SET {type_name} = '{poly_type}'"
            )

            context.operations.execute(
                f"ALTER TABLE {table} ALTER COLUMN {type_name} "
                f"SET DEFAULT 'generic'"
            )

            context.operations.execute(
                f'ALTER TABLE {table} ALTER COLUMN {type_name} SET NOT NULL'
            )


@upgrade_task('Add function column to commission memberships')
def add_function_column_to_commission_memberships(
    context: UpgradeContext
) -> None:
    if not context.has_column('par_commission_memberships', 'function'):
        context.operations.add_column(
            'par_commission_memberships',
            Column('function', Text, nullable=True, default=None)
        )


@upgrade_task('Add start/end columns to meetings')
def add_start_end_columns_to_meetings(
    context: UpgradeContext
) -> None:
    if not context.has_column('par_meetings', 'start_datetime'):
        context.operations.add_column(
            'par_meetings',
            Column('start_datetime', UTCDateTime, nullable=True)
        )
    if not context.has_column('par_meetings', 'end_datetime'):
        context.operations.add_column(
            'par_meetings',
            Column('end_datetime', UTCDateTime, nullable=True)
        )


@upgrade_task('Remove old pas tables')
def remove_old_pas_tables(
        context: UpgradeContext
) -> None:

    tablenames = [
        'pas_attendence',
        'pas_changes',
        'pas_commission_memberships',
        'pas_commissions',
        'pas_import_logs',
        'pas_legislative_periods',
        'pas_parliamentarian_roles',
        'pas_parliamentarians',
        'pas_parliamentary_groups',
        'pas_parties',
        'pas_rate_sets',
        'pas_settlements',
    ]

    for tablename in tablenames:
        if context.has_table(tablename):
            context.operations.execute(
                f'DROP TABLE IF EXISTS {tablename} CASCADE')
