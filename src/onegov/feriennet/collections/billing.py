from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.activity import BookingCollection
from onegov.activity import Invoice, InvoiceItem, InvoiceReference
from onegov.activity import InvoiceCollection
from onegov.core.orm import as_selectable, as_selectable_from_path
from onegov.core.utils import module_path, Bunch
from onegov.user import User
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from ulid import ulid


class BillingCollection:

    def __init__(self, request, period,
                 username=None, expand=False, state=None):
        self.request = request
        self.session = request.session
        self.app = request.app
        self.period = period
        self.username = username
        self.expand = expand
        self.invoices = request.app.invoice_collection(
            user_id=self.user_id,
            period_id=self.period.id
        )
        self.state = state

    @property
    def user_id(self):
        if self.username:
            return self.app.user_ids_by_name[self.username]

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(
            self.request, period, self.username, self.expand, self.state)

    def for_username(self, username):
        return self.__class__(
            self.request, self.period, username, self.expand, self.state)

    def for_expand(self, expand):
        return self.__class__(
            self.request, self.period, self.username, expand, self.state)

    def for_state(self, state):
        return self.__class__(
            self.request, self.period, self.username, self.expand, state)

    @property
    def invoices_by_period_query(self):
        return as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/invoices_by_period.sql'))

    @property
    def invoices_by_period(self):
        invoices = self.invoices_by_period_query.c

        query = select(invoices).where(invoices.period_id == self.period_id)

        if self.username:
            query = query.where(invoices.username == self.username)

        if self.state in ('paid', 'unpaid'):
            query = query.where(invoices.paid == (self.state == 'paid'))

        return self.session.execute(query)

    @property
    def bills(self):
        bills = OrderedDict()
        invoices = self.invoices_by_period

        for username, items_ in groupby(invoices, lambda i: i.username):
            items = tuple(items_)
            first = items[0]

            bills[username] = Bunch(
                items=items,
                first=first,
                id=first.id,
                invoice_id=first.invoice_id,
                title=first.realname or first.username,
                paid=first.invoice_paid,
                total=first.invoice_amount,
                outstanding=first.invoice_outstanding,
                discourage_changes=first.invoice_changes == 'discouraged',
                disable_changes=first.invoice_changes == 'impossible',
                has_online_payments=first.has_online_payments
            )

        return bills

    @property
    def total(self):
        # bills can technically be negative, which is not useful for us
        zero = Decimal("0.00")
        return max(zero, self.invoices.total_amount or zero)

    @property
    def outstanding(self):
        zero = Decimal("0.00")
        return max(zero, self.invoices.outstanding_amount or zero)

    def add_position(self, users, text, amount, group):

        # only add these positions to people who actually have an invoice
        invoices = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.username.in_(users))

        # each time we add a position, we group it uniquely using a family
        family = f"{group}-{ulid()}"
        count = 0

        for invoice in invoices:
            count += 1
            invoice.add(
                group=group,
                text=text,
                unit=amount,
                quantity=1,
                paid=False,
                family=family
            )

        return count

    def add_manual_position(self, users, text, amount):
        return self.add_position(users, text, amount, group='manual')

    def include_donation(self, text, user_id, amount):
        """ Includes a donation for the given user and period.

        Unlike manual positions, donations are supposed to be off/on per
        period. Therefore this interface is somewhat different and has an
        exclude_donation counterpart.

        """

        # an invoice is required
        invoice = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.id == user_id)\
            .options(joinedload(Invoice.items))\
            .one()

        # if there's an existing donation, update it
        for item in invoice.items:
            if item.group == 'donation':
                assert not item.paid

                item.unit = amount
                item.text = text
                return

        # if there's no donation, add it
        return invoice.add(
            group='donation',
            text=text,
            unit=amount,
            quantity=1,
            paid=False
        )

    def exclude_donation(self, user_id):
        invoice = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.id == user_id)\
            .options(joinedload(Invoice.items))\
            .first()

        if not invoice:
            return

        donations = (i for i in invoice.items if i.group == 'donation')
        donation = next(donations, None)

        if donation and not donation.paid:
            self.session.delete(donation)
            return True

        return False

    def create_invoices(self, all_inclusive_booking_text=None):
        assert not self.period.finalized

        if self.period.all_inclusive and self.period.booking_cost:
            assert all_inclusive_booking_text

        # speed up some lookups
        session = self.session
        period = self.period
        invoices = self.invoices

        # delete all existing invoices
        invoice_ids = invoices.query().with_entities(Invoice.id).subquery()

        def delete_queries():
            yield session.query(InvoiceReference).filter(
                InvoiceReference.invoice_id.in_(invoice_ids))

            yield session.query(InvoiceItem).filter(
                InvoiceItem.invoice_id.in_(invoice_ids))

            yield invoices.query()

        for q in delete_queries():
            q.delete('fetch')

        # regenerate the invoices
        bookings = BookingCollection(session, period_id=period.id)

        q = bookings.query().with_entities(
            Booking.username,
            Booking.cost,
            Booking.occasion_id,
            Booking.attendee_id,
        )
        q = q.filter(Booking.state == 'accepted')

        # create the invoices/items
        bridge = BookingInvoiceBridge(self.session, period)

        for booking in q:
            bridge.process(booking)

        bridge.complete(all_inclusive_booking_text)


class BookingInvoiceBridge:
    """ Creates invoices from bookings.

    Should be used in a two-phase process, with one exception:

    1. The bookings are processed using `process`.
    2. Premiums are applied by calling `complete`.

    The exception is if you want to simply process a single booking after
    the premiums have been processed already. This is an exception for admins
    which may add bookings after all bills have been processed already.

    """

    def __init__(self, session, period):
        # tracks attendees which had at least one booking added through the
        # bridge (even if said booking was free)
        self.processed_attendees = set()

        # init auxiliary tools
        self.session = session
        self.period = period
        self.invoices = InvoiceCollection(session)

        # preload data
        self.activities = {
            r.id: (
                r.Activity.title,
                r.Activity.user.data.get('organisation', '')
            )
            for r in session.query(Occasion.id, Activity).join(Activity)
        }

        # holds invoices which existed already
        self.existing = {
            i.user.username: i for i in self.invoices.query()
             .options(joinedload(Invoice.user))
             .filter(Invoice.period_id == period.id)
        }

        # holds attendee ids which already had at least one item in this period
        stmt = as_selectable("""
            SELECT DISTINCT
                "group",    -- Text
                "username", -- Text
                period_id   -- UUID
            FROM invoice_items

            LEFT JOIN invoices
                ON invoice_items.invoice_id = invoices.id

            LEFT JOIN users
                ON invoices.user_id = users.id

            WHERE "group" != 'manual'
        """)
        self.billed_attendees = {
            (r.username, r.group) for r in session.execute(
                select(stmt.c).where(stmt.c.period_id == period.id)
            )
        }

        self.attendees = {
            a.id: (a.name, a.username)
            for a in session.query(
                Attendee.id,
                Attendee.name,
                Attendee.username
            )
        }

        self.users = dict(session.query(User.username, User.id))

    def process(self, booking):
        """ Processes a single booking. This may be a tuple that includes
        the following fields, though a model may also work:

        * `Booking.username`
        * `Booking.cost`
        * `Booking.occasion_id`
        * `Booking.attendee_id`

        """

        if booking.username not in self.existing:
            self.existing[booking.username] = self.invoices.add(
                period_id=self.period.id,
                user_id=self.users[booking.username],
                flush=False,
                optimistic=True
            )

        self.processed_attendees.add(booking.attendee_id)

        if self.period.pay_organiser_directly or not booking.cost:
            return

        self.existing[booking.username].add(
            group=self.attendees[booking.attendee_id][0],
            text=self.activities[booking.occasion_id][0],
            organizer=self.activities[booking.occasion_id][1],
            unit=booking.cost,
            quantity=1,
            flush=False
        )

    def complete(self, all_inclusive_booking_text):
        """ Finalises the processed bookings. """

        if not self.period.all_inclusive or not self.period.booking_cost:
            return

        for id, (attendee, username) in self.attendees.items():
            if id in self.processed_attendees:
                if (username, attendee) not in self.billed_attendees:
                    self.existing[username].add(
                        group=attendee,
                        text=all_inclusive_booking_text,
                        unit=self.period.booking_cost,
                        quantity=1,
                        flush=False
                    )
