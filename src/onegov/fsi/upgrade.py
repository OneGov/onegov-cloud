""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column, ARRAY, Text, Boolean

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task


@upgrade_task('Remove department column')
def remove_department_column(context):
    if context.has_column('fsi_attendees', 'department'):
        context.operations.drop_column('fsi_attendees', 'department')


@upgrade_task('Fix wrong json type')
def fix_wrong_json_type(context):
    context.session.execute("""
        ALTER TABLE fsi_attendees
        ALTER COLUMN meta
        SET DATA TYPE jsonb
        USING meta::jsonb
    """)


@upgrade_task('Delete attendee title')
def delete_attendee_title(context):
    if context.has_column('fsi_attendees', 'title'):
        context.operations.drop_column('fsi_attendees', 'title')


@upgrade_task('Add attendee permissions col')
def add_attendee_permissions_col(context):
    if not context.has_column('fsi_attendees', 'permissions'):
        context.operations.add_column(
            'fsi_attendees',
            Column('permissions', ARRAY(Text), default=list)
        )


@upgrade_task('Make Notification.text nullable')
def make_notification_text_null(context):
    if context.has_column('fsi_notification_templates', 'text'):
        context.operations.alter_column(
            'fsi_notification_templates', 'text', nullable=True)


@upgrade_task('Adds last sent to notification template')
def add_last_sent_to_notifaction_templates(context):
    if not context.has_column('fsi_notification_templates', 'last_sent'):
        context.operations.add_column(
            'fsi_notification_templates',
            Column('last_sent', UTCDateTime)
        )


@upgrade_task('Remove sent col in reservation')
def remove_reservation_email_ts(context):
    cols = 'invitation_sent', 'reminder_sent', 'cancellation_sent', 'info_sent'

    for col in cols:

        if context.has_column('fsi_reservations', col):
            context.operations.drop_column('fsi_reservations', col)


@upgrade_task('Make Notification.subject nullable')
def make_notification_subject_null(context):
    if context.has_column('fsi_notification_templates', 'subject'):
        context.operations.alter_column(
            'fsi_notification_templates', 'subject', nullable=True)


@upgrade_task('Make course_event.presenter_email nullable')
def nullable_event_presenter_email(context):
    if context.has_column('fsi_course_events', 'presenter_email'):
        context.operations.alter_column(
            'fsi_course_events', 'presenter_email', nullable=True)


@upgrade_task('Drop CourseEvent start-end unique constraint')
def remove_course_event_uc(context):
    if context.has_table('fsi_course_events'):
        context.operations.drop_constraint(
            '_start_end_uc', 'fsi_course_events')


@upgrade_task('Adds locked_for_subscriptions property')
def add_event_property_locked(context):
    if not context.has_column('fsi_course_events', 'locked_for_subscriptions'):
        context.add_column_with_defaults(
            'fsi_course_events',
            Column('locked_for_subscriptions', Boolean,
                   nullable=False, default=True),
            default=lambda x: False)
