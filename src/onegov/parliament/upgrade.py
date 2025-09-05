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


@upgrade_task('Add type column to parliament models 2nd attempt')
def add_type_column_to_parliament_models(
        context: UpgradeContext
) -> None:
    # this is only needed as on the first attempt type columns and
    # mapper args were missing on quite some models and additional models
    # were identified afterwards

    for table, type_name, poly_type in (
            ('par_attendence', 'poly_type', 'pas_attendence'),
            ('par_changes', 'type', 'pas_change'),
            ('par_commission_memberships', 'type', 'pas_commission_membership'),
            ('par_commissions', 'poly_type', 'pas_commission'),
            ('par_legislative_periods', 'type', 'pas_legislative_period'),
            ('par_meeting_items', 'type', 'pas_meeting_items'),
            ('par_parliamentarian_roles', 'type', 'pas_parliamentarian_role'),
            ('par_parliamentarians', 'type', 'pas_parliamentarian'),
            ('par_parliamentary_groups', 'type', 'pas_parliamentary_group'),
            ('par_parties', 'type', 'pas_party'),
            ('par_political_businesses', 'type', 'pas_political_businesses'),
            ('par_political_business_participants', 'type', 'pas_political_business_participants')
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

        # verify
        # if context.has_column(table, type_name):
        #     click.secho(f'Column {type_name} added to {table}', fg='green')
        # else:
        #     click.secho(f'Column {type_name} not added to {table}', fg='red')
        #     raise ValueError('Verification failed')


# @upgrade_task('PAR Fix RIS and PAS table inconsistencies')
# def par_fix_ris_and_pas_table_inconsistencies(
#     context: UpgradeContext
# ) -> None:
#
#     # copy all items from still existing pas_attendence to par_attendence
#
#     ## NOTE: copying commissions is not needed as the data in par_commissions is better
#     # commissions prior attendence
#     # # FIXME: prevent duplicates or delete entries prior copying?
#     # if context.has_table('par_commissions') and context.has_table('pas_commissions'):
#     #     context.operations.execute('''
#     #        INSERT INTO par_commissions (id, name, start, "end", "type", meta, content, created, modified, external_kub_id, poly_type)
#     #        SELECT a.id, a.name, a.start, a.end, 'normal', a.meta, a.content, a.created, a.modified, a.external_kub_id, 'pas_commission'
#     #        FROM pas_commissions a;
#     #    ''')
#
#     # parliamentarians prior attendence
#     # FIXME: prevent duplicates or delete entries prior copying?
#     if context.has_table('par_parliamentarians') and context.has_table('pas_parliamentarians'):
#         # delete before copying to prevent duplicates
#         context.operations.execute('DELETE FROM par_parliamentarians;')
#
#         context.operations.execute('''
#            INSERT INTO par_parliamentarians (type, id, external_kub_id, first_name, last_name, personnel_number, contract_number, gender, shipping_method, shipping_address, shipping_address_addition, shipping_address_city, private_address, private_address_addition, private_address_zip_code, private_address_city, date_of_birth, date_of_death, place_of_origin, party, occupation, academic_title, salutation, salutation_for_address, salutation_for_letter, forwarding_of_bills, phone_private, phone_mobile, phone_business, email_primary, email_secondary, website, remarks, meta, content, created, modified)
#               SELECT 'pas_parliamentarian', a.id, a.external_kub_id, a.first_name, a.last_name, a.personnel_number, a.contract_number, a.gender, a.shipping_method, a.shipping_address, a.shipping_address_addition, a.shipping_address_city, a.private_address, a.private_address_addition, a.private_address_zip_code, a.private_address_city, a.date_of_birth, a.date_of_death, a.place_of_origin, a.party, a.occupation, a.academic_title, a.salutation, a.salutation_for_address, a.salutation_for_letter, a.forwarding_of_bills, a.phone_private, a.phone_mobile, a.phone_business, a.email_primary, a.email_secondary, a.website, a.remarks, a.meta, a.content, a.created, a.modified
#               FROM pas_parliamentarians a;
#          ''')
#
#     # FIXME: prevent duplicates or delete entries prior copying?
#     if context.has_table('par_attendence') and context.has_table('pas_attendence'):
#        context.operations.execute('''
#             INSERT INTO par_attendence (id, date, duration, type, parliamentarian_id, commission_id, created, modified)
#             SELECT a.id, a.date, a.duration, a.type::text::par_attendence_type, a.parliamentarian_id, a.commission_id, a.created, a.modified
#             FROM pas_attendence a
#             INNER JOIN par_commissions c ON a.commission_id = c.id;
#         ''')
