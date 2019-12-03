""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column, ARRAY, Text

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
