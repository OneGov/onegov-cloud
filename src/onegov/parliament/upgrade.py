"""Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Text

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


@upgrade_task('Add type column to parliament models',
              requires='onegov.parliament:Introduce parliament module: '
                       'rename pas tables')
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
