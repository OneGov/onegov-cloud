""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.orm.types import JSON, UUID, UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from sqlalchemy import ARRAY, Column, Boolean, Enum, Float, ForeignKey, Integer
from sqlalchemy import Text


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


@upgrade_task('Add status column to translator_time_reports')
def add_status_column_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'status'):
        status_enum = Enum('pending', 'confirmed', name='time_report_status')
        if not context.has_enum('time_report_status'):
            status_enum.create(context.operations.get_bind())
        context.add_column_with_defaults(
            table='translator_time_reports',
            column=Column(
                'status', status_enum, nullable=False, default='pending'
            ),
            default=lambda x: 'pending',
        )


@upgrade_task('Add created_by_id to translator_time_reports')
def add_created_by_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'created_by_id'):
        context.operations.add_column(
            'translator_time_reports',
            Column(
                'created_by_id',
                UUID,
                ForeignKey('users.id', ondelete='SET NULL'),
                nullable=True,
            ),
        )


@upgrade_task('Convert Float to Numeric for monetary columns')
def convert_float_to_numeric_in_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return

    monetary_columns = [
        'hourly_rate',
        'travel_compensation',
        'total_compensation',
    ]

    for col in monetary_columns:
        if context.has_column('translator_time_reports', col):
            precision, scale = 10, 2

            context.operations.execute(
                f'ALTER TABLE translator_time_reports '
                f'ALTER COLUMN {col} TYPE NUMERIC({precision},{scale}) '
                f'USING {col}::NUMERIC({precision},{scale})'
            )


@upgrade_task('Add surcharge_types array column to time reports')
def add_surcharge_types_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'surcharge_types'):
        context.operations.add_column(
            'translator_time_reports',
            Column('surcharge_types', ARRAY(Text), nullable=True),
        )


@upgrade_task('Add start and end datetime to time reports')
def add_start_end_datetime_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'start'):
        context.operations.add_column(
            'translator_time_reports',
            Column('start', UTCDateTime, nullable=True),
        )
    if not context.has_column('translator_time_reports', 'end'):
        context.operations.add_column(
            'translator_time_reports',
            Column('end', UTCDateTime, nullable=True),
        )


@upgrade_task('Add break_time column to time reports')
def add_break_time_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'break_time'):
        context.add_column_with_defaults(
            table='translator_time_reports',
            column=Column('break_time', Integer, nullable=False, default=0),
            default=lambda x: 0,
        )


@upgrade_task('Add night_minutes column to time reports')
def add_night_minutes_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'night_minutes'):
        context.add_column_with_defaults(
            table='translator_time_reports',
            column=Column('night_minutes', Integer, nullable=False, default=0),
            default=lambda x: 0,
        )


@upgrade_task('Add weekend_holiday_minutes column to time reports')
def add_weekend_holiday_minutes_to_time_reports(
    context: UpgradeContext,
) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column(
        'translator_time_reports', 'weekend_holiday_minutes'
    ):
        context.add_column_with_defaults(
            table='translator_time_reports',
            column=Column(
                'weekend_holiday_minutes', Integer, nullable=False, default=0
            ),
            default=lambda x: 0,
        )


@upgrade_task('Remove surcharge_percentage column from time reports')
def remove_surcharge_percentage_from_time_reports(
    context: UpgradeContext,
) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if context.has_column('translator_time_reports', 'surcharge_percentage'):
        context.operations.drop_column(
            'translator_time_reports', 'surcharge_percentage'
        )


@upgrade_task('Remove old night_hours column from time reports')
def remove_night_hours_from_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if context.has_column('translator_time_reports', 'night_hours'):
        context.operations.drop_column(
            'translator_time_reports', 'night_hours')


@upgrade_task('Add assignment_location column to time reports')
def add_assignment_location_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column(
        'translator_time_reports', 'assignment_location'
    ):
        context.operations.add_column(
            'translator_time_reports',
            Column('assignment_location', Text, nullable=True)
        )


@upgrade_task('Add travel_distance column to time reports')
def add_travel_distance_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'travel_distance'):
        context.operations.add_column(
            'translator_time_reports',
            Column('travel_distance', Float(precision=2), nullable=True)
        )


@upgrade_task('Add finanzstelle column to time reports')
def add_finanzstelle_to_time_reports(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if not context.has_column('translator_time_reports', 'finanzstelle'):
        context.operations.add_column(
            'translator_time_reports',
            Column('finanzstelle', Text, nullable=True),
        )


@upgrade_task('Make assignment_type non-nullable in time reports')
def make_assignment_type_non_nullable(context: UpgradeContext) -> None:
    if not context.has_table('translator_time_reports'):
        return
    if context.has_column('translator_time_reports', 'assignment_type'):
        context.operations.alter_column(
            'translator_time_reports', 'assignment_type', nullable=False
        )
