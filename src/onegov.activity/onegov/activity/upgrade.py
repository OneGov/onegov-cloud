""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import hashlib
import string

from itertools import chain
from onegov.activity import ActivityCollection
from onegov.activity import Booking
from onegov.activity import InvoiceCollection
from onegov.activity import InvoiceItem
from onegov.activity import InvoiceReference
from onegov.activity import Occasion
from onegov.activity import Period
from onegov.activity import PeriodCollection
from onegov.core.crypto import random_token
from onegov.core.orm.sql import as_selectable
from onegov.core.orm.types import UUID, JSON
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import Bunch
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import desc
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import joinedload


@upgrade_task('Rebuild bookings')
def rebuild_bookings(context):
    # having not created any bookings yet, we can rebuild them
    context.operations.drop_table('bookings')


@upgrade_task('Add period_id to bookings')
def add_period_id_to_bookings(context):

    context.operations.add_column('bookings', Column(
        'period_id', UUID, ForeignKey("periods.id"), nullable=True
    ))

    bookings = context.session.query(Booking)
    bookings = bookings.options(joinedload(Booking.occasion))

    for booking in bookings:
        booking.period_id = booking.occasion.period_id

    context.session.flush()
    context.operations.alter_column('bookings', 'period_id', nullable=False)


@upgrade_task('Change booking states')
def change_booking_states(context):

    new_type = Enum(
        'open',
        'blocked',
        'accepted',
        'denied',
        'cancelled',
        name='booking_state'
    )

    op = context.operations

    op.execute("""
        ALTER TABLE bookings ALTER COLUMN state TYPE Text;
        UPDATE bookings SET state = 'open' WHERE state = 'unconfirmed';
        DROP TYPE booking_state;
    """)

    new_type.create(op.get_bind())

    op.execute("""
        ALTER TABLE bookings ALTER COLUMN state
        TYPE booking_state USING state::text::booking_state;
    """)


@upgrade_task('Add confirmed flag to period')
def add_confirmed_flag_to_period(context):
    context.operations.add_column('periods', Column(
        'confirmed', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(Period):
        period.confirmed = False

    context.session.flush()
    context.operations.alter_column('periods', 'confirmed', nullable=False)


@upgrade_task('Add data column to period')
def add_data_column_to_period(context):
    context.operations.add_column('periods', Column(
        'data', JSON, nullable=True, default=dict
    ))

    for period in context.session.query(Period):
        period.data = {}

    context.session.flush()
    context.operations.alter_column('periods', 'data', nullable=False)


@upgrade_task('Add attendee_count column to occasion')
def add_attendee_count_column_to_occasion(context):
    context.operations.add_column('occasions', Column(
        'attendee_count', Integer, nullable=True, default=0
    ))

    for occasion in context.session.query(Occasion):
        occasion.attendee_count = len(occasion.accepted)

    context.session.flush()
    context.operations.alter_column(
        'occasions', 'attendee_count', nullable=False)


@upgrade_task('Add finalized flag to period')
def add_finalized_flag_to_period(context):
    context.operations.add_column('periods', Column(
        'finalized', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(Period):
        period.finalized = False

    context.session.flush()
    context.operations.alter_column('periods', 'finalized', nullable=False)


@upgrade_task('Add payment model columns')
def add_payment_model_columns(context):
    context.operations.add_column('periods', Column(
        'max_bookings_per_attendee', Integer, nullable=True
    ))

    context.operations.add_column('periods', Column(
        'booking_cost', Numeric(precision=8, scale=2), nullable=True
    ))

    context.operations.add_column('periods', Column(
        'all_inclusive', Boolean, nullable=True
    ))

    for period in context.session.query(Period):
        period.all_inclusive = False

    context.session.flush()
    context.operations.alter_column('periods', 'all_inclusive', nullable=False)

    context.operations.add_column('occasions', Column(
        'cost', Numeric(precision=8, scale=2), nullable=True
    ))

    context.operations.add_column('bookings', Column(
        'cost', Numeric(precision=8, scale=2), nullable=True
    ))


@upgrade_task('Add cancelled flag to occasion')
def add_cancelled_flag_to_occasion(context):
    context.operations.add_column('occasions', Column(
        'cancelled', Boolean, nullable=True
    ))

    for occasion in context.session.query(Occasion):
        occasion.cancelled = False

    context.session.flush()
    context.operations.alter_column('occasions', 'cancelled', nullable=False)


@upgrade_task('Add code field to invoice items')
def add_code_field_to_invoice_items(context):
    context.operations.add_column('invoice_items', Column(
        'code', Text, nullable=True
    ))

    for i in context.session.query(InvoiceItem):
        i.code = 'q' + ''.join((
            hashlib.sha1((
                i.invoice + i.username).encode('utf-8')
            ).hexdigest()[:5],
            hashlib.sha1(
                i.username.encode('utf-8')
            ).hexdigest()[:5]
        ))

    context.session.flush()
    context.operations.alter_column('invoice_items', 'code', nullable=False)


@upgrade_task('Add source field to invoice items')
def add_source_field_to_invoice_items(context):
    if not context.has_column('invoice_items', 'source'):
        context.operations.add_column('invoice_items', Column(
            'source', Text, nullable=True
        ))


@upgrade_task('Add gender/notes fields to attendees')
def add_gender_notes_fields_to_attendees(context):
    if not context.has_column('attendees', 'gender'):
        context.operations.add_column('attendees', Column(
            'gender', Text, nullable=True
        ))

    if not context.has_column('attendees', 'notes'):
        context.operations.add_column('attendees', Column(
            'notes', Text, nullable=True
        ))


@upgrade_task('Support multiple dates per occasion')
def support_multiple_dates_per_occasion(context):
    context.operations.drop_constraint('start_before_end', 'occasions')

    for name in ('durations', 'order'):
        context.operations.add_column(
            'occasions', Column(name, Integer, server_default="0"))
        context.operations.alter_column(
            'occasions', name, server_default=None)

    context.session.execute("""
        INSERT INTO occasion_dates ("timezone", "start", "end", "occasion_id")
        SELECT "timezone", "start", "end", "id" FROM occasions
    """)

    context.session.flush()

    # update dates
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()

    for name in ('start', 'end', 'timezone'):
        context.operations.drop_column('occasions', name)


@upgrade_task('Adds minutes_between to period')
def adds_minutes_between_to_period(context):
    context.operations.add_column('periods', Column(
        'minutes_between', Integer, nullable=True, server_default='0'))
    context.operations.alter_column(
        'periods', 'minutes_between', server_default=None)


@upgrade_task('Adds exclude_from_overlap_check to period')
def adds_exclude_from_overlap_check_to_period(context):
    context.operations.add_column('occasions', Column(
        'exclude_from_overlap_check', Boolean, nullable=False,
        server_default='FALSE'))
    context.operations.alter_column(
        'occasions', 'exclude_from_overlap_check', server_default=None)


@upgrade_task('Adds deadlines to period')
def adds_deadlines_to_period(context):
    if not context.has_column('periods', 'deadline_date'):
        context.operations.add_column('periods', Column(
            'deadline_date', Date, nullable=True
        ))
    if not context.has_column('periods', 'deadline_days'):
        context.operations.add_column('periods', Column(
            'deadline_days', Integer, nullable=True
        ))


@upgrade_task('Adds limit to attendee')
def adds_limit_to_attendee(context):
    if not context.has_column('attendees', 'limit'):
        context.operations.add_column('attendees', Column(
            'limit', Integer, nullable=True
        ))


@upgrade_task('Introduce location/meeting_point')
def introduce_location_meeting_point(context):
    if not context.has_column('activities', 'location'):
        context.operations.add_column('activities', Column(
            'location', Text, nullable=True
        ))
    if not context.has_column('occasions', 'meeting_point'):
        context.operations.alter_column(
            'occasions', 'location', new_column_name='meeting_point')


@upgrade_task('Add active days')
def add_active_days(context):
    if context.has_column('activities', 'active_days'):
        assert context.has_column('occasions', 'active_days')
        return

    context.session.execute(
        'CREATE AGGREGATE "{}".array_cat_agg(anyarray) '
        '(SFUNC=array_cat, STYPE=anyarray)'.format(
            context.schema
        )
    )

    context.operations.add_column('activities', Column(
        'active_days', ARRAY(Integer), nullable=True
    ))

    context.operations.add_column('occasions', Column(
        'active_days', ARRAY(Integer), nullable=True
    ))

    context.session.flush()

    # update dates
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Add active days index')
def add_active_days_index(context):
    context.operations.create_index(
        'inverted_active_days', 'activities', ['active_days'],
        postgresql_using='gin'
    )


@upgrade_task('Removed denied activity state')
def remove_denied_activity_state(context):

    new_type = Enum(
        'preview',
        'proposed',
        'accepted',
        'archived',
        name='activity_state'
    )

    op = context.operations

    op.execute("""
        ALTER TABLE activities ALTER COLUMN state TYPE Text;
        UPDATE activities SET state = 'archived' WHERE state = 'denied';
        DROP TYPE activity_state;
    """)

    new_type.create(op.get_bind())

    op.execute("""
        ALTER TABLE activities ALTER COLUMN state
        TYPE activity_state USING state::text::activity_state;
    """)


@upgrade_task('Add weekdays')
def add_weekdays(context):
    if context.has_column('activities', 'weekdays'):
        assert context.has_column('occasions', 'weekdays')
        return

    context.operations.add_column('activities', Column(
        'weekdays', ARRAY(Integer), nullable=True
    ))

    context.operations.add_column('occasions', Column(
        'weekdays', ARRAY(Integer), nullable=True
    ))

    context.session.flush()

    # update dates
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Add weekdays index')
def add_weekdays_index(context):
    context.operations.create_index(
        'inverted_weekdays', 'activities', ['weekdays'],
        postgresql_using='gin'
    )


@upgrade_task('Extract thumbnails')
def extract_thumbnails(context):
    for activity in ActivityCollection(context.session).query():
        activity.content_observer(None)


@upgrade_task('Retroactively create publication requests')
def retroactively_create_publication_requests(context):
    activities = ActivityCollection(context.session).query()

    if not activities.count():
        return False

    periods = PeriodCollection(context.session)

    p = periods.query()
    p = p.order_by(desc(Period.active), desc(Period.execution_start))
    p = p.first()

    assert p, "an active period is required"

    for activity in activities:
        activity.create_publication_request(p, id=activity.id)


@upgrade_task('Add archived flag to period')
def add_archived_flag_to_period(context):
    context.operations.add_column('periods', Column(
        'archived', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(Period):
        period.archived = False

    context.session.flush()
    context.operations.alter_column('periods', 'archived', nullable=False)


@upgrade_task('Extract municipality from activities')
def add_municipality_column_to_activites(context):
    context.operations.add_column('activities', Column(
        'municipality', Text, nullable=True
    ))

    for activity in ActivityCollection(context.session).query():
        activity.location_observer(None)


@upgrade_task('Add family to invoice items')
def add_family_to_invoice_items(context):
    context.operations.add_column('invoice_items', Column(
        'family', Text, nullable=True
    ))


@upgrade_task('Add subscription_token to attendeeds')
def add_subscription(context):
    context.add_column_with_defaults(
        table='attendees',
        column=Column('subscription_token', Text, nullable=False, unique=True),
        default=lambda attendee: random_token()
    )


@upgrade_task('Add alignment to periods')
def add_alignment(context):
    if not context.has_column('periods', 'alignment'):
        context.operations.add_column('periods', Column(
            'alignment', Text, nullable=True
        ))


@upgrade_task('Update duration categories')
def update_duration_categories(context):
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Rename occasion durations to the singular')
def rename_occasion_durations_to_the_singular(context):
    context.operations.alter_column(
        table_name='occasions',
        column_name='durations',
        new_column_name='duration'
    )

    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Add pay_organiser_directly column')
def add_pay_organiser_directly_column(context):
    context.add_column_with_defaults(
        table='periods',
        column=Column('pay_organiser_directly', Boolean, nullable=False),
        default=False
    )


@upgrade_task('Remove activity aggregates')
def remove_activity_aggregates(context):
    context.operations.drop_index('inverted_weekdays', 'activities')
    context.operations.drop_index('inverted_active_days', 'activities')
    context.operations.drop_column('activities', 'durations')
    context.operations.drop_column('activities', 'ages')
    context.operations.drop_column('activities', 'period_ids')
    context.operations.drop_column('activities', 'active_days')
    context.operations.drop_column('activities', 'weekdays')


@upgrade_task('Add invoices')
def add_invoices(context):
    if not context.has_column('invoice_items', 'code'):
        return

    if not context.has_column('invoices', 'code'):
        context.operations.add_column('invoices', Column(
            'code', Text, nullable=True
        ))

    stmt = as_selectable("""
        SELECT
            invoice_items.id,           -- UUID
            code,                       -- Text
            invoice::uuid AS period_id, -- UUID
            users.id AS user_id         -- UUID
        FROM invoice_items
        LEFT JOIN users ON invoice_items.username = users.username
    """)

    invoices = InvoiceCollection(context.session)

    mapping = {
        r.id: Bunch(record=r, invoice=None)
        for r in context.session.execute(select(stmt.c))
    }

    created = {}

    for m in mapping.values():
        id = (m.record.period_id, m.record.user_id)

        if id in created:
            m.invoice = created[id]
            continue

        created[id] = m.invoice = invoices.add(
            period_id=m.record.period_id,
            user_id=m.record.user_id,
            code=m.record.code)

    def invoice_id(item):
        return mapping[item.id].invoice.id

    context.add_column_with_defaults(
        table='invoice_items',
        column=Column('invoice_id', UUID, ForeignKey('invoices.id')),
        default=invoice_id
    )

    context.session.flush()

    context.operations.drop_column('invoice_items', 'username')
    context.operations.drop_column('invoice_items', 'code')
    context.operations.drop_column('invoice_items', 'invoice')


@upgrade_task('Add invoice references')
def add_invoice_references(context):
    if not context.has_column('invoices', 'code'):
        return

    # legacy functions obsolete after this migration
    CODE_TO_ESR_MAPPING = {
        character: '{:02d}'.format(value) for value, character in chain(
            enumerate(string.digits, start=1),
            enumerate(string.ascii_lowercase, start=11)
        )
    }

    def generate_checksum(number):
        table = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
        carry = 0

        for n in str(number):
            carry = table[(carry + int(n)) % 10]

        return (10 - carry) % 10

    def append_checksum(number):
        number = str(number)
        return number + str(generate_checksum(number))

    def encode_invoice_code(code):
        version = '1'

        blocks = [version]

        for char in code:
            if char in CODE_TO_ESR_MAPPING:
                blocks.append(CODE_TO_ESR_MAPPING[char])
            else:
                raise RuntimeError(
                    "Invalid character {} in {}".format(char, code))

        return append_checksum('{:0>26}'.format(''.join(blocks)))

    stmt = as_selectable("""
        SELECT
            invoices.id,           -- UUID
            invoices.code          -- Text
        FROM invoices
    """)

    invoices = context.session.execute(select(stmt.c))

    # the references might have been created already in the previous upgrade
    # step, if it was executed with the latest release
    context.session.execute('DELETE FROM invoice_references')

    for invoice in invoices:
        context.session.add(
            InvoiceReference(
                invoice_id=invoice.id,
                reference=invoice.code,
                schema='feriennet-v1',
                bucket='feriennet-v1'
            )
        )

        context.session.add(
            InvoiceReference(
                invoice_id=invoice.id,
                reference=encode_invoice_code(invoice.code),
                schema='esr-v1',
                bucket='esr-v1'
            )
        )

    context.operations.drop_column('invoices', 'code')


@upgrade_task('Add invoice reference bucket')
def add_invoice_reference_bucket(context):
    if context.has_column('invoice_references', 'bucket'):
        return

    context.add_column_with_defaults(
        table='invoice_references',
        column=Column('bucket', Text),
        default=lambda r: r.schema
    )

    context.operations.drop_constraint(
        'unique_schema_invoice_id', 'invoice_references')

    context.operations.create_unique_constraint(
        'unique_bucket_invoice_id', 'invoice_references', (
            'bucket', 'invoice_id'
        ))


@upgrade_task('Adds cancellation deadlines to period')
def adds_cancellation_deadlines_to_period(context):
    if not context.has_column('periods', 'cancellation_date'):
        context.operations.add_column('periods', Column(
            'cancellation_date', Date, nullable=True
        ))
    if not context.has_column('periods', 'cancellation_days'):
        context.operations.add_column('periods', Column(
            'cancellation_days', Integer, nullable=True
        ))


@upgrade_task('Make group_code nullable')
def make_group_code_nullable(context):
    context.operations.alter_column('bookings', 'group_code', nullable=True)

    # nobody uses groups yet, so we can safely reset it all to NULL
    context.operations.execute("UPDATE bookings SET group_code = NULL")


@upgrade_task('Adds exempt_from_booking_limit to occasion')
def adds_exempt_from_booking_limit_to_occasion(context):
    context.add_column_with_defaults(
        table='occasions',
        column=Column('exempt_from_booking_limit', Boolean, nullable=False),
        default=False
    )


@upgrade_task('Adds score to bookings')
def adds_score_to_bookings(context):
    context.add_column_with_defaults(
        table='bookings',
        column=Column('score', Numeric(precision=14, scale=9), nullable=False),
        default=0
    )
