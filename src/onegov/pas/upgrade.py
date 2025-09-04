"""Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from __future__ import annotations

from sqlalchemy import Column, Text
from onegov.core.orm.types import UUID
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
            context.add_column_with_defaults(
                'pas_parliamentarians',
                Column(
                    'party',
                    Text,
                    nullable=True
                ),
                default=None
            )


@upgrade_task('Add bulk_edit_id column to pas_attendence')
def add_bulk_edit_id_column_to_pas_attendence(context: UpgradeContext) -> None:
    if context.has_table('pas_attendence'):
        if not context.has_column('pas_attendence', 'bulk_edit_id'):
            context.add_column_with_defaults(
                'pas_attendence',
                Column(
                    'bulk_edit_id',
                    UUID,
                    nullable=True
                ),
                default=None
            )

@upgrade_task('Add bulk_edit_id column to par_attendence')
def add_bulk_edit_id_column_to_par_attendence(context: UpgradeContext) -> None:
    if context.has_table('par_attendence'):
        if not context.has_column('par_attendence', 'bulk_edit_id'):
            context.add_column_with_defaults(
                'par_attendence',
                Column(
                    'bulk_edit_id',
                    UUID,
                    nullable=True
                ),
                default=None
            )
