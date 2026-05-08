""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.fsi.models.course_attendee import external_attendee_org
from sqlalchemy import text, Boolean, Column, Text, ARRAY


@upgrade_task('Remove department column')
def remove_department_column(context: UpgradeContext) -> None:
    if context.has_column('fsi_attendees', 'department'):
        context.operations.drop_column('fsi_attendees', 'department')


@upgrade_task('Fix wrong json type')
def fix_wrong_json_type(context: UpgradeContext) -> None:
    context.session.execute(text("""
        ALTER TABLE fsi_attendees
        ALTER COLUMN meta
        SET DATA TYPE jsonb
        USING meta::jsonb
    """))


@upgrade_task('Delete attendee title')
def delete_attendee_title(context: UpgradeContext) -> None:
    if context.has_column('fsi_attendees', 'title'):
        context.operations.drop_column('fsi_attendees', 'title')


@upgrade_task('Add attendee permissions col')
def add_attendee_permissions_col(context: UpgradeContext) -> None:
    if not context.has_column('fsi_attendees', 'permissions'):
        context.add_column_with_defaults(
            'fsi_attendees',
            Column('permissions', ARRAY(Text), default=list),
            default=lambda x: []  # type: ignore
        )


@upgrade_task('Make Notification.text nullable')
def make_notification_text_null(context: UpgradeContext) -> None:
    if context.has_column('fsi_notification_templates', 'text'):
        context.operations.alter_column(
            'fsi_notification_templates', 'text', nullable=True)


@upgrade_task('Adds last sent to notification template')
def add_last_sent_to_notifaction_templates(context: UpgradeContext) -> None:
    if not context.has_column('fsi_notification_templates', 'last_sent'):
        context.operations.add_column(
            'fsi_notification_templates',
            Column('last_sent', UTCDateTime)
        )


@upgrade_task('Remove sent col in reservation')
def remove_reservation_email_ts(context: UpgradeContext) -> None:
    cols = 'invitation_sent', 'reminder_sent', 'cancellation_sent', 'info_sent'

    for col in cols:

        if context.has_column('fsi_reservations', col):
            context.operations.drop_column('fsi_reservations', col)


@upgrade_task('Make Notification.subject nullable')
def make_notification_subject_null(context: UpgradeContext) -> None:
    if context.has_column('fsi_notification_templates', 'subject'):
        context.operations.alter_column(
            'fsi_notification_templates', 'subject', nullable=True)


@upgrade_task('Make course_event.presenter_email nullable')
def nullable_event_presenter_email(context: UpgradeContext) -> None:
    if context.has_column('fsi_course_events', 'presenter_email'):
        context.operations.alter_column(
            'fsi_course_events', 'presenter_email', nullable=True)


@upgrade_task('Drop CourseEvent start-end unique constraint')
def remove_course_event_uc(context: UpgradeContext) -> None:
    if context.has_table('fsi_course_events'):
        context.operations.drop_constraint(
            '_start_end_uc', 'fsi_course_events')


@upgrade_task('Adds locked_for_subscriptions property')
def add_event_property_locked(context: UpgradeContext) -> None:
    if not context.has_column('fsi_course_events', 'locked_for_subscriptions'):
        context.add_column_with_defaults(
            'fsi_course_events',
            Column('locked_for_subscriptions', Boolean,
                   nullable=False, default=True),
            default=lambda x: False)


@upgrade_task('Adds hidden_from_public to course')
def add_hidden_from_public_in_course(context: UpgradeContext) -> None:
    if not context.has_column('fsi_courses', 'hidden_from_public'):
        context.add_column_with_defaults(
            'fsi_courses',
            Column('hidden_from_public', Boolean, nullable=False,
                   default=False),
            default=lambda x: False)


@upgrade_task('Adds source_id to attendee')
def add_source_id_to_attendee(context: UpgradeContext) -> None:
    if not context.has_column('fsi_attendees', 'source_id'):
        context.operations.add_column(
            'fsi_attendees',
            Column('source_id', Text, nullable=True))

    context.session.execute(text("""
        UPDATE fsi_attendees t2
        SET source_id = t1.source_id
        FROM users t1
        WHERE  t2.user_id = t1.id
    """))


@upgrade_task('Change refresh_interval to integer representing years')
def change_refresh_interval(context: UpgradeContext) -> None:
    if not context.has_column('fsi_courses', 'refresh_interval'):
        return
    if context.is_empty_table('fsi_courses'):
        return

    context.session.execute(text("""
        ALTER TABLE fsi_courses ALTER COLUMN refresh_interval
        TYPE INT USING extract(days FROM refresh_interval) / 30 / 12::int
        """))


@upgrade_task('Adds organisation to external attendees')
def add_org_to_external_attendee(context: UpgradeContext) -> None:
    context.session.execute(text(f"""
        UPDATE fsi_attendees
        SET organisation = '{external_attendee_org}'
        WHERE fsi_attendees.user_id IS NULL;
    """))


@upgrade_task('Adds permission for external attendees to role editor')
def append_org_to_external_attendee(context: UpgradeContext) -> None:
    if not context.has_column('fsi_attendees', 'permissions'):
        return
    context.session.execute(text(f"""
        UPDATE fsi_attendees
        SET permissions = array_append(permissions, '{external_attendee_org}')
        WHERE fsi_attendees.id IN (
                SELECT a.id
                FROM fsi_attendees a
                JOIN users u on a.user_id = u.id
                WHERE u.role = 'editor'
                AND NOT a.permissions @> ARRAY ['{external_attendee_org}']
            );
    """))


@upgrade_task('Adds active property to attendees')
def add_active_property_to_attendees(context: UpgradeContext) -> None:
    if not context.has_column('fsi_attendees', 'active'):
        context.add_column_with_defaults(
            'fsi_attendees',
            Column('active', Boolean, nullable=False, default=True),
            default=lambda x: True
        )


@upgrade_task('Adds evaluation_url to course')
def add_evaluation_url_to_course(context: UpgradeContext) -> None:
    if not context.has_column('fsi_courses', 'evaluation_url'):
        context.add_column_with_defaults(
            'fsi_courses',
            Column('evaluation_url', Text, nullable=True),
            default=lambda x: None  # type: ignore
        )
