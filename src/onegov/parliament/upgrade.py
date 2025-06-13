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


@upgrade_task('Add type column to parliament models 3')
def add_type_column_to_parliament_models(
        context: UpgradeContext
) -> None:
    for table, type_name in (
        ('par_attendence', 'party_type'),
        ('par_changes', 'change_type'),
        ('par_commission_memberships', 'membership_type'),
        ('par_commissions', 'commission_type'),
        ('par_legislative_periods', 'legislative_period_type'),
        ('par_parliamentarian_roles', 'role_type'),
        ('par_parliamentarians', 'parliamentarian_type'),
        ('par_parliamentary_groups', 'group_type'),
        ('par_parties', 'party_type'),
    ):
        if not context.has_column(table, type_name):
            context.operations.add_column(
                table,
                Column(type_name, Text, nullable=False, default='generic')
            )
