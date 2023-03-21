""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import re
import textwrap

from sqlalchemy import Column, ARRAY, Text, Boolean

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.people import Person


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
        context.add_column_with_defaults(
            'fsi_attendees',
            Column('permissions', ARRAY(Text), default=list),
            default=lambda x: []
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


@upgrade_task('Adds hidden_from_public to course')
def add_hidden_from_public_in_course(context):
    if not context.has_column('fsi_courses', 'hidden_from_public'):
        context.add_column_with_defaults(
            'fsi_courses',
            Column('hidden_from_public', Boolean, nullable=False,
                   default=False),
            default=lambda x: False)


@upgrade_task('Adds source_id to attendee')
def add_source_id_to_attendee(context):
    if not context.has_column('fsi_attendees', 'source_id'):
        context.operations.add_column(
            'fsi_attendees',
            Column('source_id', Text, nullable=True))

    context.session.execute("""
        UPDATE fsi_attendees t2
        SET source_id = t1.source_id
        FROM users t1
        WHERE  t2.user_id = t1.id
    """)


@upgrade_task('Change refresh_interval to integer representing years')
def change_refresh_interval(context):
    if not context.has_column('fsi_courses', 'refresh_interval'):
        return
    if context.is_empty_table('fsi_courses'):
        return

    context.session.execute(textwrap.dedent("""\
        ALTER TABLE fsi_courses ALTER COLUMN refresh_interval
        TYPE INT USING extract(days FROM refresh_interval) / 30 / 12::int
        """))


@upgrade_task('Adds organisation to external attendees')
def add_org_to_external_attendee(context):
    context.session.execute(textwrap.dedent(f"""\
        UPDATE fsi_attendees
        SET organisation = '{external_attendee_org}'
        WHERE fsi_attendees.user_id IS NULL;
    """))


@upgrade_task('Adds permission for external attendees to role editor')
def append_org_to_external_attendee(context):
    if not context.has_column('fsi_attendees', 'permissions'):
        return
    context.session.execute(textwrap.dedent(f"""
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
def add_active_property_to_attendees(context):
    if not context.has_column('fsi_attendees', 'active'):
        context.add_column_with_defaults(
            'fsi_attendees',
            Column('active', Boolean, nullable=False, default=True),
            default=lambda x: True
        )


p2 = re.compile(r'(.*), (.*)Postadresse: (.*), (.*)')
p3 = re.compile(r'(.*), (Postfach), (.*)')
p4 = re.compile(r'(.*), (.*), (.*)')
p1 = re.compile(r'(.*), (.*)')
p5 = re.compile(r'([A-Za-z ]*) ?(\d+[a-z]?)?')  # street name and optional
# building number


def parse_and_split_address_field(address):
    """
    Parsing the `address` field to split into location address and code/city
    as well as postal address and code/city.

    :param address:str
    :return: tuple: (location_address, location_code_city,
                     postal_address, postal_code_city)
    """
    location_addr = ''
    location_pcc = ''
    postal_addr = ''
    postal_pcc = ''

    # sanitize address
    if ';' in address:
        address = address.replace('; ', '')
        address = address.replace(';', '')

    if not address:
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    if m := p2.match(address):
        location_addr = m.group(1)
        location_pcc = m.group(2)
        postal_addr = m.group(3)
        postal_pcc = m.group(4)
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    if m := p3.match(address):
        postal_addr = m.group(1) + '\n' + m.group(2)
        postal_pcc = m.group(3)
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    if m := p4.match(address):
        postal_addr = m.group(1) + '\n' + m.group(2)
        postal_pcc = m.group(3)
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    if m := p1.match(address):
        postal_addr = m.group(1)
        postal_pcc = m.group(2)
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    if m := p5.match(address):
        postal_addr = m.group(1)
        if m.group(2):
            postal_addr += f'{m.group(2)}'
        return (location_addr, location_pcc, postal_addr, postal_pcc)

    # default
    print(f'*** parse_and_split_address_field: no match found for address:'
          f' {address}')
    return location_addr, location_pcc, postal_addr, postal_pcc


@upgrade_task('ogc-966 extend agency and person tables with more fields 1')
def extend_agency_and_person_with_more_fields(context):
    ################################################################
    # add columns to table 'agencies'
    agencies_columns = ['email', 'phone', 'phone_direct', 'website',
                        'location_address', 'location_code_city',
                        'postal_address', 'postal_code_city',
                        'opening_hours']
    table = 'agencies'

    for column in agencies_columns:
        print(f'Checking table {table} for column {column} .. ')
        if not context.has_column(table, column):
            print(' -> column added')
            context.add_column_with_defaults(
                'agencies',
                Column(column, Text, nullable=True),
                default=lambda x: ''
            )
        else:
            print(' -> column exists')

    print()
    context.session.flush()

    ################################################################
    # add columns to table 'people'
    people_columns = ['location_address', 'location_code_city',
                      'postal_address', 'postal_code_city']
    table = 'people'

    for column in people_columns:
        print(f'Checking table {table} for column {column} .. ')
        if not context.has_column(table, column):
            # print(f'Adding column {column} to table {table}..')
            print(' -> column added')
            context.add_column_with_defaults(
                'people',
                Column(column, Text, nullable=True),
                default=lambda x: ''
            )
        else:
            print(' -> column exists')

    print(f"Migrate data from table {table} column 'address' field to "
          f"'location_address', 'location_code_city', 'postal_address' and "
          f"'postal_code_city ..")
    for person in context.session.query(Person):
        if not person.address:
            continue

        person.location_address, person.location_code_city, \
            person.postal_address, person.postal_code_city = \
            parse_and_split_address_field(person.address)

    context.session.flush()
