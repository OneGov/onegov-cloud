""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

import string

from itertools import chain
from onegov.activity import ActivityCollection
from onegov.activity import ActivityInvoiceItem
from onegov.activity import Attendee
from onegov.activity import BookingPeriod
from onegov.activity import BookingPeriodCollection
from onegov.activity import BookingPeriodInvoice
from onegov.activity import BookingPeriodInvoiceCollection
from onegov.activity import Occasion
from onegov.activity import OccasionNeed
from onegov.core.crypto import random_token
from onegov.core.orm.sql import as_selectable
from onegov.core.orm.types import UUID
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.core.utils import Bunch
from onegov.pay import InvoiceReference
from onegov.user import User
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY


@upgrade_task('Add gender/notes fields to attendees')
def add_gender_notes_fields_to_attendees(context: UpgradeContext) -> None:
    if not context.has_column('attendees', 'gender'):
        context.operations.add_column('attendees', Column(
            'gender', Text, nullable=True
        ))

    if not context.has_column('attendees', 'notes'):
        context.operations.add_column('attendees', Column(
            'notes', Text, nullable=True
        ))


@upgrade_task('Support multiple dates per occasion')
def support_multiple_dates_per_occasion(context: UpgradeContext) -> None:
    context.operations.drop_constraint('start_before_end', 'occasions')

    for name in ('durations', 'order'):
        context.operations.add_column(
            'occasions', Column(name, Integer, server_default='0'))
        context.operations.alter_column(
            'occasions', name, server_default=None)

    context.session.execute(text("""
        INSERT INTO occasion_dates ("timezone", "start", "end", "occasion_id")
        SELECT "timezone", "start", "end", "id" FROM occasions
    """))

    context.session.flush()

    # update dates
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()

    for name in ('start', 'end', 'timezone'):
        context.operations.drop_column('occasions', name)


@upgrade_task('Adds minutes_between to period')
def adds_minutes_between_to_period(context: UpgradeContext) -> None:
    context.operations.add_column('periods', Column(
        'minutes_between', Integer, nullable=True, server_default='0'))
    context.operations.alter_column(
        'periods', 'minutes_between', server_default=None)


@upgrade_task('Adds exclude_from_overlap_check to period')
def adds_exclude_from_overlap_check_to_period(context: UpgradeContext) -> None:
    context.operations.add_column('occasions', Column(
        'exclude_from_overlap_check', Boolean, nullable=False,
        server_default='FALSE'))
    context.operations.alter_column(
        'occasions', 'exclude_from_overlap_check', server_default=None)


@upgrade_task('Adds deadlines to period')
def adds_deadlines_to_period(context: UpgradeContext) -> None:
    if not context.has_column('periods', 'deadline_date'):
        context.operations.add_column('periods', Column(
            'deadline_date', Date, nullable=True
        ))
    if not context.has_column('periods', 'deadline_days'):
        context.operations.add_column('periods', Column(
            'deadline_days', Integer, nullable=True
        ))


@upgrade_task('Adds limit to attendee')
def adds_limit_to_attendee(context: UpgradeContext) -> None:
    if not context.has_column('attendees', 'limit'):
        context.operations.add_column('attendees', Column(
            'limit', Integer, nullable=True
        ))


@upgrade_task('Introduce location/meeting_point')
def introduce_location_meeting_point(context: UpgradeContext) -> None:
    if not context.has_column('activities', 'location'):
        context.operations.add_column('activities', Column(
            'location', Text, nullable=True
        ))
    if not context.has_column('occasions', 'meeting_point'):
        context.operations.alter_column(
            'occasions', 'location', new_column_name='meeting_point')


@upgrade_task('Add active days')
def add_active_days(context: UpgradeContext) -> None:
    if context.has_column('activities', 'active_days'):
        assert context.has_column('occasions', 'active_days')
        return

    # This will be removed in an upgrade step further down again and is not
    # compatible with postgres 13- and 14+.
    # context.session.execute(text(
    #     'CREATE AGGREGATE "{}".array_cat_agg(anyarray) '
    #     '(SFUNC=array_cat, STYPE=anyarray)'.format(
    #         context.schema
    #     )
    # ))

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
def add_active_days_index(context: UpgradeContext) -> None:
    context.operations.create_index(
        'inverted_active_days', 'activities', ['active_days'],
        postgresql_using='gin'
    )


@upgrade_task('Removed denied activity state')
def remove_denied_activity_state(context: UpgradeContext) -> None:

    new_type = Enum(
        'preview',
        'proposed',
        'accepted',
        'archived',
        name='activity_state'
    )

    op = context.operations

    op.execute(text("""
        ALTER TABLE activities ALTER COLUMN state TYPE Text;
        UPDATE activities SET state = 'archived' WHERE state = 'denied';
        DROP TYPE activity_state;
    """))

    new_type.create(op.get_bind())

    op.execute(text("""
        ALTER TABLE activities ALTER COLUMN state
        TYPE activity_state USING state::text::activity_state;
    """))


@upgrade_task('Add weekdays')
def add_weekdays(context: UpgradeContext) -> None:
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
def add_weekdays_index(context: UpgradeContext) -> None:
    context.operations.create_index(
        'inverted_weekdays', 'activities', ['weekdays'],
        postgresql_using='gin'
    )


@upgrade_task('Extract thumbnails')
def extract_thumbnails(context: UpgradeContext) -> None:
    for activity in ActivityCollection(context.session).query():
        activity.content_observer(None)


@upgrade_task('Retroactively create publication requests')
def retroactively_create_publication_requests(context: UpgradeContext) -> None:
    activities = ActivityCollection(context.session).query()

    if not activities.count():
        return

    periods = BookingPeriodCollection(context.session)

    pq = periods.query()
    pq = pq.order_by(
        BookingPeriod.active.desc(),
        BookingPeriod.execution_start.desc()
    )
    p = pq.first()

    assert p, 'an active period is required'

    for activity in activities:
        activity.create_publication_request(p, id=activity.id)


@upgrade_task('Add archived flag to period')
def add_archived_flag_to_period(context: UpgradeContext) -> None:
    context.operations.add_column('periods', Column(
        'archived', Boolean, nullable=True, default=False
    ))

    for period in context.session.query(BookingPeriod):
        period.archived = False

    context.session.flush()
    context.operations.alter_column('periods', 'archived', nullable=False)


@upgrade_task('Extract municipality from activities')
def add_municipality_column_to_activites(context: UpgradeContext) -> None:
    context.operations.add_column('activities', Column(
        'municipality', Text, nullable=True
    ))

    for activity in ActivityCollection(context.session).query():
        activity.location_observer(None)


@upgrade_task('Add family to invoice items')
def add_family_to_invoice_items(context: UpgradeContext) -> None:
    context.operations.add_column('invoice_items', Column(
        'family', Text, nullable=True
    ))


@upgrade_task('Add subscription_token to attendeeds')
def add_subscription(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='attendees',
        column=Column('subscription_token', Text, nullable=False, unique=True),
        default=lambda attendee: random_token()
    )


@upgrade_task('Add alignment to periods')
def add_alignment(context: UpgradeContext) -> None:
    if not context.has_column('periods', 'alignment'):
        context.operations.add_column('periods', Column(
            'alignment', Text, nullable=True
        ))


@upgrade_task('Update duration categories')
def update_duration_categories(context: UpgradeContext) -> None:
    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Rename occasion durations to the singular')
def rename_occasion_durations_to_the_singular(context: UpgradeContext) -> None:
    context.operations.alter_column(
        table_name='occasions',
        column_name='durations',
        new_column_name='duration'
    )

    for occasion in context.session.query(Occasion):
        occasion.on_date_change()


@upgrade_task('Add pay_organiser_directly column')
def add_pay_organiser_directly_column(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='periods',
        column=Column('pay_organiser_directly', Boolean, nullable=False),
        default=False
    )


@upgrade_task('Remove activity aggregates')
def remove_activity_aggregates(context: UpgradeContext) -> None:
    context.operations.drop_index('inverted_weekdays', 'activities')
    context.operations.drop_index('inverted_active_days', 'activities')
    context.operations.drop_column('activities', 'durations')
    context.operations.drop_column('activities', 'ages')
    context.operations.drop_column('activities', 'period_ids')
    context.operations.drop_column('activities', 'active_days')
    context.operations.drop_column('activities', 'weekdays')


@upgrade_task('Add invoices')
def add_invoices(context: UpgradeContext) -> None:
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

    invoices = BookingPeriodInvoiceCollection(context.session)

    mapping = {
        r.id: Bunch(record=r, invoice=None)
        for r in context.session.execute(select(stmt.c))
    }

    created = {}  # type:ignore[var-annotated]

    for m in mapping.values():
        id = (m.record.period_id, m.record.user_id)

        if id in created:
            m.invoice = created[id]
            continue

        created[id] = m.invoice = invoices.add(  # type:ignore[call-arg]
            period_id=m.record.period_id,
            user_id=m.record.user_id,
            code=m.record.code)

    def invoice_id(item):  # type:ignore[no-untyped-def]
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
def add_invoice_references(context: UpgradeContext) -> None:
    if not context.has_column('invoices', 'code'):
        return

    # legacy functions obsolete after this migration
    CODE_TO_ESR_MAPPING = {  # noqa: N806
        character: '{:02d}'.format(value) for value, character in chain(
            enumerate(string.digits, start=1),
            enumerate(string.ascii_lowercase, start=11)
        )
    }

    def generate_checksum(number: str) -> int:
        table = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
        carry = 0

        for n in str(number):
            carry = table[(carry + int(n)) % 10]

        return (10 - carry) % 10

    def append_checksum(number: str) -> str:
        number = str(number)
        return number + str(generate_checksum(number))

    def encode_invoice_code(code: str) -> str:
        version = '1'

        blocks = [version]

        for char in code:
            if char in CODE_TO_ESR_MAPPING:
                blocks.append(CODE_TO_ESR_MAPPING[char])
            else:
                raise RuntimeError(
                    'Invalid character {} in {}'.format(char, code))

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
    context.session.execute(text('DELETE FROM invoice_references'))

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
def add_invoice_reference_bucket(context: UpgradeContext) -> None:
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
def adds_cancellation_deadlines_to_period(context: UpgradeContext) -> None:
    if not context.has_column('periods', 'cancellation_date'):
        context.operations.add_column('periods', Column(
            'cancellation_date', Date, nullable=True
        ))
    if not context.has_column('periods', 'cancellation_days'):
        context.operations.add_column('periods', Column(
            'cancellation_days', Integer, nullable=True
        ))


@upgrade_task('Make group_code nullable')
def make_group_code_nullable(context: UpgradeContext) -> None:
    context.operations.alter_column('bookings', 'group_code', nullable=True)

    # nobody uses groups yet, so we can safely reset it all to NULL
    context.operations.execute(text('UPDATE bookings SET group_code = NULL'))


@upgrade_task('Adds exempt_from_booking_limit to occasion')
def adds_exempt_from_booking_limit_to_occasion(
    context: UpgradeContext
) -> None:
    context.add_column_with_defaults(
        table='occasions',
        column=Column('exempt_from_booking_limit', Boolean, nullable=False),
        default=False
    )


@upgrade_task('Adds score to bookings')
def adds_score_to_bookings(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='bookings',
        column=Column('score', Numeric(precision=14, scale=9), nullable=False),
        default=0  # type:ignore[arg-type]
    )


@upgrade_task('Drop occasion.active column')
def drop_occasion_active_column(context: UpgradeContext) -> None:
    context.operations.drop_column('occasions', 'active')


@upgrade_task('Add age barrier type')
def add_age_barrier_type(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='periods',
        column=Column('age_barrier_type', Text),
        default='exact'
    )


@upgrade_task('Add booking phase dates')
def add_booking_phase_dates(context: UpgradeContext) -> None:
    context.operations.drop_constraint('period_date_order', 'periods')

    context.add_column_with_defaults(
        table='periods',
        column=Column('booking_start', Date, nullable=False),
        default=lambda p: p.prebooking_end
    )

    context.add_column_with_defaults(
        table='periods',
        column=Column('booking_end', Date, nullable=False),
        default=lambda p: p.execution_start
    )

    context.operations.create_check_constraint(
        'period_date_order',
        'periods',
        """
            prebooking_start
            <= prebooking_end AND prebooking_end
            <= booking_start AND booking_start
            <= booking_end AND booking_end
            <= execution_start AND execution_start
            <= execution_end
        """
    )


@upgrade_task('Add confirmable and finalizable columns')
def add_confirmable_and_finalizable_columns(context: UpgradeContext) -> None:
    for name in ('confirmable', 'finalizable'):
        context.add_column_with_defaults(
            table='periods',
            column=Column(name, Boolean, nullable=False),
            default=True
        )


@upgrade_task('Improve period dates constraint')
def improve_period_dates_constraint(context: UpgradeContext) -> None:
    context.operations.drop_constraint('period_date_order', 'periods')

    context.operations.create_check_constraint(
        'period_date_order',
        'periods',
        (
            # ranges should be valid
            'prebooking_start <= prebooking_end AND '
            'booking_start <= booking_end AND '
            'execution_start <= execution_end AND '

            # pre-booking must happen before booking and execution
            'prebooking_end <= booking_start AND '
            'prebooking_end <= execution_start AND '

            # booking and execution may overlap, but the execution cannot
            # start before booking begins
            'booking_start <= execution_start AND '
            'booking_end <= execution_end'
        ),
    )


@upgrade_task('Drop deadline_date')
def drop_deadline_date(context: UpgradeContext) -> None:
    context.session.execute(text("""
            UPDATE periods SET booking_end = deadline_date
            WHERE deadline_date IS NOT NULL
              AND execution_start <= deadline_date
              AND deadline_date <= execution_end
        """))

    context.operations.drop_column('periods', 'deadline_date')


@upgrade_task('Add book_finalized')
def book_finalized(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='periods',
        column=Column('book_finalized', Boolean, nullable=False),
        default=False
    )


@upgrade_task('Add occasion booking_cost')
def add_occasion_booking_cost(context: UpgradeContext) -> None:
    context.operations.add_column('occasions', column=Column(
        'booking_cost', Numeric(precision=8, scale=2), nullable=True))


@upgrade_task('Add seeking_voluneteers column')
def add_seeking_volunteers_column(context: UpgradeContext) -> None:
    seeking_volunteers = {
        n.occasion_id for n in context.session.query(
            OccasionNeed.occasion_id).distinct(OccasionNeed.occasion_id)}

    def is_seeking_volunteers(occasion: Occasion) -> bool:
        return occasion.id in seeking_volunteers

    context.add_column_with_defaults(
        table='occasions',
        column=Column('seeking_volunteers', Boolean, nullable=False),
        default=is_seeking_volunteers
    )


@upgrade_task('Add occasion need accept_signups toggle')
def add_occasion_need_public_toggle(context: UpgradeContext) -> None:
    context.add_column_with_defaults(
        table='occasion_needs',
        column=Column('accept_signups', Boolean, nullable=False),
        default=False
    )

    for occasion in context.session.query(Occasion):
        occasion.seeking_volunteers = False


@upgrade_task('Add invoice item payment date')
def add_invoice_item_payment_date(context: UpgradeContext) -> None:
    if not context.has_column('invoice_items', 'payment_date'):
        context.operations.add_column(
            'invoice_items',
            column=Column('payment_date', Date, nullable=True)
        )


@upgrade_task('Make activity polymorphic type non-nullable')
def make_activity_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    if context.has_table('activities'):
        context.operations.execute(text("""
            UPDATE activities SET type = 'generic' WHERE type IS NULL;
        """))

        context.operations.alter_column('activities', 'type', nullable=False)


@upgrade_task('Cleanup activity aggregates')
def cleanup_activity_aggregates(context: UpgradeContext) -> None:
    context.operations.execute(text(f"""
        DROP AGGREGATE IF EXISTS "{context.schema}".array_cat_agg(anyarray);
    """))


@upgrade_task('Add differing attendee address')
def add__differing_attendee_address(context: UpgradeContext) -> None:
    if not context.has_column('attendees', 'differing_address'):
        context.operations.add_column(
            'attendees',
            column=Column('differing_address', Boolean, nullable=True)
        )
    if not context.has_column('attendees', 'address'):
        context.operations.add_column(
            'attendees',
            column=Column('address', Text, nullable=True)
        )
    if not context.has_column('attendees', 'zip_code'):
        context.operations.add_column(
            'attendees',
            column=Column('zip_code', Text, nullable=True)
        )
    if not context.has_column('attendees', 'place'):
        context.operations.add_column(
            'attendees',
            column=Column('place', Text, nullable=True)
        )
    if not context.has_column('attendees', 'political_municipality'):
        context.operations.add_column(
            'attendees',
            column=Column('political_municipality', Text, nullable=True)
        )


@upgrade_task('Add invoice item organizer')
def add_invoice_item_organizer(context: UpgradeContext) -> None:
    if not context.has_column('invoice_items', 'organizer'):
        context.operations.add_column(
            'invoice_items',
            column=Column('organizer', Text, nullable=True)
        )


@upgrade_task('Add attendee id to invoice item')
def add_attendee_id_to_invoice_item(context: UpgradeContext) -> None:
    if not context.has_column('invoice_items', 'attendee_id'):
        context.operations.add_column('invoice_items', Column(
            'attendee_id', UUID, ForeignKey('attendees.id'), nullable=True
        ))


@upgrade_task('Fill in attendee ids')
def fill_in_attendee_ids_1(context: UpgradeContext) -> None:
    q = context.session.query(
        ActivityInvoiceItem, Attendee
    ).join(BookingPeriodInvoice).join(User)
    q = q.join(
        Attendee,
        func.lower(ActivityInvoiceItem.group) == func.lower(Attendee.name)
    )
    q = q.filter(User.username == Attendee.username)
    q = q.filter(User.id == BookingPeriodInvoice.user_id)
    q = q.filter(ActivityInvoiceItem.attendee_id.is_(None))

    for item, attendee in q:
        item.attendee_id = attendee.id


@upgrade_task('Add siwsspass id column to attendee')
def add_swisspass_id_column_to_attendee(context: UpgradeContext) -> None:
    if not context.has_column('attendees', 'swisspass'):
        context.operations.add_column(
            'attendees',
            column=Column('swisspass', Text, nullable=True)
        )


@upgrade_task('Update invoice tables for polymorphism')
def update_invoice_tables_for_polymorphism(context: UpgradeContext) -> None:
    if not context.has_column('invoices', 'type'):
        context.operations.add_column('invoices', Column(
            'type',
            Text,
            nullable=False,
            server_default='booking_period'
        ))
        context.operations.alter_column(
            'invoices',
            'type',
            server_default=None
        )
        # make existing columns nullable
        context.operations.alter_column(
            'invoices',
            'period_id',
            nullable=True
        )
        context.operations.alter_column(
            'invoices',
            'user_id',
            nullable=True
        )
        # but add a check constraint enforcing the same invariant
        if not context.has_constraint(
            'invoices',
            'ck_booking_period_required_columns',
            'CHECK'
        ):
            context.operations.create_check_constraint(
                'ck_booking_period_required_columns',
                'invoices',
                '(period_id IS NOT NULL AND user_id IS NOT NULL)'
                "OR type != 'booking_period'"
            )
    if not context.has_column('invoice_items', 'type'):
        context.operations.add_column('invoice_items', Column(
            'type',
            Text,
            nullable=False,
            server_default='activity'
        ))
        context.operations.alter_column(
            'invoice_items',
            'type',
            server_default=None
        )
