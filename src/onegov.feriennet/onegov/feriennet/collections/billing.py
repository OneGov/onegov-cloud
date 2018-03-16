import hashlib

from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, Attendee, Booking, Occasion, InvoiceItem
from onegov.activity import BookingCollection, InvoiceItemCollection
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path, Bunch
from onegov.pay import Price
from sqlalchemy import select, distinct
from ulid import ulid


class BillingDetails(object):

    __slots__ = (
        'id', 'items', 'paid', 'total', 'title', 'outstanding', 'first',
        'discourage_changes', 'disable_changes', 'has_online_payments'
    )

    def __init__(self, title, items):
        self.title = title
        self.items = items
        self.total = Decimal("0.00")
        self.outstanding = Decimal("0.00")
        self.paid = True
        self.first = None
        self.discourage_changes = False
        self.disable_changes = False
        self.has_online_payments = False

        def tally(item):
            self.total += item.amount

            if not item.paid:
                self.paid = False
                self.outstanding += item.amount

            if item.discourage_changes:
                self.discourage_changes = True

            if item.disable_changes:
                self.disable_changes = True

            if item.source and item.source != 'xml':
                self.has_online_payments = True

            if not self.first:
                self.first = item

            return item

        self.items = {
            group: tuple(groupitems) for group, groupitems
            in groupby((tally(i) for i in items), lambda i: i.group)
        }

        self.total = max(self.total, Decimal("0.00"))
        self.outstanding = max(self.outstanding, Decimal("0.00"))

        if not self.outstanding:
            self.paid = True

        self.id = self.invoice_id(self.first)

    @property
    def price(self):
        return Price(self.outstanding, 'CHF')

    @staticmethod
    def invoice_id(item):
        components = (item.invoice, item.username)
        return hashlib.md5(''.join(components).encode('utf-8')).hexdigest()


class BillingCollection(object):

    def __init__(self, session, period, username=None, expand=False):
        self.session = session
        self.period = period
        self.username = username
        self.expand = expand

        self.invoice_items = InvoiceItemCollection(
            session=session,
            username=username,
            invoice=self.period.id.hex
        )

    @property
    def invoices_by_period(self):
        return as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/invoices_by_period.sql'))

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period, self.username, self.expand)

    def for_username(self, username):
        return self.__class__(self.session, self.period, username, self.expand)

    def for_expand(self, expand):
        return self.__class__(self.session, self.period, self.username, expand)

    @property
    def invoices(self):
        invoices = self.invoices_by_period.c

        query = select(invoices).where(invoices.period_id == self.period_id)

        if self.username:
            query = query.where(invoices.username == self.username)

        return self.session.execute(query)

    @property
    def bills(self):
        bills = OrderedDict()

        for username, items in groupby(self.invoices, lambda i: i.username):
            items = tuple(items)
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
        return max(zero, self.invoice_items.total or zero)

    @property
    def outstanding(self):
        zero = Decimal("0.00")
        return max(zero, self.invoice_items.outstanding or zero)

    def add_manual_position(self, users, text, amount):
        invoice = self.period.id.hex
        session = self.session

        # only add these positions to people who actually have an invoice
        useable = {
            i[0] for i in
            self.invoice_items.query().with_entities(
                distinct(InvoiceItem.username)
            )
        }

        # each time we add a manual position, we group it using a family
        family = f"manual-{ulid()}"
        count = 0

        for username in users:
            if username in useable:
                count += 1
                session.add(InvoiceItem(
                    username=username,
                    invoice=invoice,
                    group='manual',
                    text=text,
                    unit=amount,
                    quantity=1,
                    paid=False,
                    family=family
                ))

        return count

    @property
    def usernames_with_invoices(self):
        self.invoice_items.query().with_entites(InvoiceItem.username)

    def create_invoices(self, all_inclusive_booking_text=None):
        assert not self.period.finalized

        if self.period.all_inclusive and self.period.booking_cost:
            assert all_inclusive_booking_text

        # delete all existing invoice items
        invoice = self.period.id.hex
        session = self.session
        period = self.period

        for item in self.invoice_items.query():
            assert item.invoice == invoice
            session.delete(item)

        # preload data to avoid more expensive joins
        activities = {
            r.id: r.title
            for r in session.query(Occasion.id, Activity.title).join(Activity)
        }

        attendees = {
            a.id: (a.name, a.username)
            for a in session.query(
                Attendee.id,
                Attendee.name,
                Attendee.username
            )
        }

        # regenerate the bookings
        bookings = BookingCollection(session, period_id=period.id)

        q = bookings.query().with_entities(
            Booking.username,
            Booking.cost,
            Booking.occasion_id,
            Booking.attendee_id,
        )
        q = q.filter(Booking.state == 'accepted')

        # keep track of the attendees which have at least one booking (even
        # if said booking is free)
        actual_attendees = set()

        for booking in q:
            actual_attendees.add(booking.attendee_id)

            if booking.cost:
                session.add(InvoiceItem(
                    username=booking.username,
                    invoice=invoice,
                    group=attendees[booking.attendee_id][0],
                    text=activities[booking.occasion_id],
                    unit=booking.cost,
                    quantity=1
                ))

        # add the all inclusive booking costs if necessary
        if period.all_inclusive and period.booking_cost:
            for id, (attendee, username) in attendees.items():
                if id in actual_attendees:
                    session.add(InvoiceItem(
                        username=username,
                        invoice=invoice,
                        group=attendee,
                        text=all_inclusive_booking_text,
                        unit=period.booking_cost,
                        quantity=1
                    ))
